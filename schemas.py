"""Typed hand-offs between agents (architecture rule 1).

Two flavours of the research report exist on purpose:

* ``Draft*`` models are what the MODEL fills in. Evidence cites sources by
  number only (``source_ids``) - the model never sees or writes a URL.
* The final models are what CODE produces after validation: the numbers are
  replaced by real ``Source`` objects taken from Gemini's grounding metadata.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------
# Sources and evidence (final, code-produced)
# --------------------------------------------------------------------------
class Source(BaseModel):
    """A web source taken from Gemini's grounding metadata, never from model text."""
    id: int
    title: str
    url: str


class Evidence(BaseModel):
    """One claim plus the real sources that back it."""
    claim: str
    sources: list[Source]


# --------------------------------------------------------------------------
# Item "cores": the fields that are identical in the draft and in the final
# --------------------------------------------------------------------------
class CompetitorCore(BaseModel):
    name: str
    what_it_does: str
    pricing: str = Field(description="Pricing model as found in the sources, or 'unknown'")
    strengths: list[str]
    weaknesses: list[str]


class AudienceCore(BaseModel):
    segment: str
    description: str
    needs: list[str]


class PainPointCore(BaseModel):
    pain: str
    who_feels_it: str
    severity: Literal["low", "medium", "high"]


class MarketSignalCore(BaseModel):
    signal: str
    direction: Literal["tailwind", "headwind", "neutral"]


# --------------------------------------------------------------------------
# Draft: what the model returns (evidence cites source numbers only)
# --------------------------------------------------------------------------
class DraftEvidence(BaseModel):
    claim: str
    source_ids: list[int] = Field(description="Numbers of the sources that support the claim")


class DraftCompetitor(CompetitorCore):
    evidence: list[DraftEvidence]


class DraftAudience(AudienceCore):
    evidence: list[DraftEvidence]


class DraftPainPoint(PainPointCore):
    evidence: list[DraftEvidence]


class DraftMarketSignal(MarketSignalCore):
    evidence: list[DraftEvidence]


class ResearchDraft(BaseModel):
    summary: str
    competitors: list[DraftCompetitor]
    audiences: list[DraftAudience]
    pain_points: list[DraftPainPoint]
    market_signals: list[DraftMarketSignal]


# --------------------------------------------------------------------------
# Final: validated by code, sources resolved
# --------------------------------------------------------------------------
class Competitor(CompetitorCore):
    evidence: list[Evidence]


class Audience(AudienceCore):
    evidence: list[Evidence]


class PainPoint(PainPointCore):
    evidence: list[Evidence]


class MarketSignal(MarketSignalCore):
    evidence: list[Evidence]


class ResearchReport(BaseModel):
    """The research agent's output - what the Product agent reads."""
    summary: str
    competitors: list[Competitor]
    audiences: list[Audience]
    pain_points: list[PainPoint]
    market_signals: list[MarketSignal]


# --------------------------------------------------------------------------
# Shared run state (saved to runs/<run_id>/state.json)
# --------------------------------------------------------------------------
class Dropped(BaseModel):
    """Anything code removed, and why (rule 6: no silent drops)."""
    kind: str          # "evidence" or "item"
    category: str      # competitors / audiences / pain_points / market_signals
    label: str         # name of the item or text of the claim
    reason: str


class RunState(BaseModel):
    run_id: str
    created_at: str
    idea: str
    status: Literal["running", "ok", "partial", "failed"] = "running"
    error: Optional[str] = None
    research: Optional[ResearchReport] = None
    sources: list[Source] = Field(default_factory=list)   # every source the search tool returned
    dropped: list[Dropped] = Field(default_factory=list)
