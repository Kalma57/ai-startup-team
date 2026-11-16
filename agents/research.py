"""Research agent.

Step A  four Google-Search-grounded calls (one per topic) -> notes + real sources
Step B  one structured call: notes -> ResearchDraft (cites source NUMBERS only)
Step C  code validates the draft and swaps numbers for real Source objects

Sources always come from Gemini's grounding metadata (rule 4); the model never
writes a URL. Anything code drops is recorded in state.dropped (rule 6).
"""
import logging
from dataclasses import dataclass, field

from google import genai
from google.genai import types

from config import Settings
from llm import call_with_retry
from schemas import (Audience, Competitor, Dropped, Evidence, MarketSignal, PainPoint,
                     ResearchDraft, ResearchReport, RunState, Source)
from state import Run

log = logging.getLogger("research")
AGENT = "research"

# One search per topic: more focused sources than a single broad search.
TOPIC_PROMPTS = {
    "competitors": (
        "Find real products that compete with or are close to this startup idea "
        "(direct competitors and adjacent apps, including local/Hebrew-market ones if relevant). "
        "For each: what it does, pricing model, strengths, weaknesses."),
    "audiences": (
        "Identify the target audience segments for this startup idea: who they are, "
        "what they need, how they currently solve the problem."),
    "pain_points": (
        "Find real user pain points and complaints in this problem space: reviews of "
        "existing apps, forum and community discussions, common frustrations."),
    "market_signals": (
        "Find market signals for this idea: market size or growth, trends, "
        "pricing benchmarks, adoption or regulatory factors, tailwinds and headwinds."),
}


# --------------------------------------------------------------------------
# Sources: global numbering across all search calls, deduplicated by URL
# --------------------------------------------------------------------------
@dataclass
class SourceRegistry:
    by_url: dict[str, Source] = field(default_factory=dict)

    def add(self, url: str, title: str) -> int:
        if url not in self.by_url:
            self.by_url[url] = Source(id=len(self.by_url) + 1, title=title or url, url=url)
        return self.by_url[url].id

    @property
    def sources(self) -> list[Source]:
        return list(self.by_url.values())

    def by_id(self) -> dict[int, Source]:
        return {s.id: s for s in self.by_url.values()}


def extract_grounding(response, registry: SourceRegistry) -> tuple[str, int]:
    """Return (notes text with [n] citation markers, number of sources found).

    Markers are inserted from grounding_supports, i.e. from the search tool's own
    mapping of text segments to the web pages that back them.
    """
    text = response.text or ""
    candidates = response.candidates or []
    meta = candidates[0].grounding_metadata if candidates else None
    if meta is None or not meta.grounding_chunks:
        return text, 0

    # chunk index (local to this response) -> global source id
    chunk_to_id: dict[int, int] = {}
    for i, chunk in enumerate(meta.grounding_chunks):
        if chunk.web and chunk.web.uri:
            chunk_to_id[i] = registry.add(chunk.web.uri, chunk.web.title or chunk.web.domain or "")

    # Insert markers back-to-front so earlier offsets stay valid. Offsets are UTF-8 bytes.
    raw = text.encode("utf-8")
    inserts = []
    for support in meta.grounding_supports or []:
        end = support.segment.end_index if support.segment else None
        ids = sorted({chunk_to_id[i] for i in (support.grounding_chunk_indices or [])
                      if i in chunk_to_id})
        if end is not None and ids:
            inserts.append((end, "".join(f"[{n}]" for n in ids)))
    for end, marker in sorted(inserts, key=lambda x: x[0], reverse=True):
        raw = raw[:end] + marker.encode("utf-8") + raw[end:]
    return raw.decode("utf-8", errors="replace"), len(chunk_to_id)


# --------------------------------------------------------------------------
# Step A: grounded search
# --------------------------------------------------------------------------
def search_topic(client: genai.Client, settings: Settings, idea: str, topic: str,
                 registry: SourceRegistry) -> str:
    prompt = (f"STARTUP IDEA:\n{idea}\n\nTASK: {TOPIC_PROMPTS[topic]}\n"
              "Be specific: name real products, quote real numbers, and say when you are unsure.")
    config = types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
    response = call_with_retry(
        lambda: client.models.generate_content(
            model=settings.research_model, contents=prompt, config=config),
        what=f"search:{topic}")
    notes, n_sources = extract_grounding(response, registry)
    if n_sources == 0:
        log.warning("Search for '%s' returned no grounded sources", topic)
    return notes


# --------------------------------------------------------------------------
# Step B: structure the notes (no search tool in this call)
# --------------------------------------------------------------------------
def structure_notes(client: genai.Client, settings: Settings, idea: str,
                    notes: dict[str, str], registry: SourceRegistry) -> ResearchDraft:
    source_list = "\n".join(f"[{s.id}] {s.title}" for s in registry.sources)
    notes_block = "\n\n".join(f"## {topic.upper()}\n{text}" for topic, text in notes.items())
    prompt = (
        f"STARTUP IDEA:\n{idea}\n\n"
        f"RESEARCH NOTES (numbers in [brackets] are source numbers):\n{notes_block}\n\n"
        f"AVAILABLE SOURCES:\n{source_list}\n\n"
        "TASK: Turn the notes into the structured report. Rules:\n"
        "- Use ONLY facts present in the notes. Do not add outside knowledge.\n"
        "- Every item needs evidence: a short claim plus source_ids (integers from the "
        "AVAILABLE SOURCES list that back that claim).\n"
        "- Never write URLs. Never invent source numbers.\n"
        "- If the notes do not support an item, leave it out.")
    config = types.GenerateContentConfig(
        response_mime_type="application/json", response_schema=ResearchDraft)
    response = call_with_retry(
        lambda: client.models.generate_content(
            model=settings.agent_model, contents=prompt, config=config),
        what="structure")
    return ResearchDraft.model_validate_json(response.text)


# --------------------------------------------------------------------------
# Step C: code validation - resolve numbers to real sources, record every drop
# --------------------------------------------------------------------------
def _resolve(evidence_list, valid: dict[int, Source], category: str, label: str,
             dropped: list[Dropped]) -> list[Evidence]:
    resolved = []
    for ev in evidence_list:
        ids = sorted({i for i in ev.source_ids if i in valid})
        bad = sorted({i for i in ev.source_ids if i not in valid})
        if bad:
            what = "evidence" if not ids else "source_id"   # whole claim lost vs only bad numbers
            dropped.append(Dropped(kind=what, category=category, label=ev.claim,
                                   reason=f"cited source numbers that do not exist: {bad}"))
        elif not ids:
            dropped.append(Dropped(kind="evidence", category=category, label=ev.claim,
                                   reason="no source cited"))
        if not ids:
            continue
        resolved.append(Evidence(claim=ev.claim, sources=[valid[i] for i in ids]))
    return resolved


def validate_draft(draft: ResearchDraft, registry: SourceRegistry
                   ) -> tuple[ResearchReport, list[Dropped]]:
    valid = registry.by_id()
    dropped: list[Dropped] = []

    def convert(items, category, label_of, cls):
        out = []
        for item in items:
            label = label_of(item)
            evidence = _resolve(item.evidence, valid, category, label, dropped)
            if not evidence:
                dropped.append(Dropped(kind="item", category=category, label=label,
                                       reason="no valid evidence left after source check"))
                continue
            data = item.model_dump(exclude={"evidence"})
            out.append(cls(**data, evidence=evidence))
        return out

    report = ResearchReport(
        summary=draft.summary,
        competitors=convert(draft.competitors, "competitors", lambda i: i.name, Competitor),
        audiences=convert(draft.audiences, "audiences", lambda i: i.segment, Audience),
        pain_points=convert(draft.pain_points, "pain_points", lambda i: i.pain, PainPoint),
        market_signals=convert(draft.market_signals, "market_signals",
                               lambda i: i.signal, MarketSignal),
    )
    return report, dropped


# --------------------------------------------------------------------------
# Entry point used by the CLI
# --------------------------------------------------------------------------
def run_research(run: Run, state: RunState, client: genai.Client, settings: Settings) -> RunState:
    registry = SourceRegistry()
    notes: dict[str, str] = {}
    try:
        # Step A
        for topic in TOPIC_PROMPTS:
            with run.step(AGENT, f"search:{topic}") as info:
                notes[topic] = search_topic(client, settings, state.idea, topic, registry)
                info["note"] = f"{len(registry.sources)} unique sources so far"
        state.sources = registry.sources
        if not registry.sources:
            raise RuntimeError("The search tool returned no grounded sources at all; "
                               "refusing to build a report without evidence.")

        # Step B
        with run.step(AGENT, "structure") as info:
            draft = structure_notes(client, settings, state.idea, notes, registry)
            info["note"] = (f"draft: {len(draft.competitors)} competitors, "
                            f"{len(draft.audiences)} audiences, {len(draft.pain_points)} pain points, "
                            f"{len(draft.market_signals)} market signals")

        # Step C
        with run.step(AGENT, "validate") as info:
            report, dropped = validate_draft(draft, registry)
            state.research, state.dropped = report, dropped
            for d in dropped:
                log.warning("DROPPED %s [%s] %r: %s", d.kind, d.category, d.label, d.reason)
            empty = [name for name in ("competitors", "audiences", "pain_points", "market_signals")
                     if not getattr(report, name)]
            state.status = "partial" if empty else "ok"
            info["note"] = f"status={state.status}, dropped={len(dropped)}, empty categories={empty}"
    except Exception as exc:
        state.status = "failed"
        state.error = f"{type(exc).__name__}: {exc}"
        log.error("Research failed: %s", state.error)
    finally:
        run.save(state)
    return state
