# AI Startup Team · סדנה · @lior.the.creator

צוות של חמישה סוכני AI שמקבל רעיון לסטארטאפ, חוקר את השוק, מתכנן מוצר, בונה דף נחיתה ובודק אותו.

**אתם לא כותבים את הקוד.** סוכן קוד (Claude Code, Gemini CLI, Antigravity) הוא הבנאי.
אתם הארכיטקטים: מגדירים דרישות, בודקים תוכניות, מריצים, קוראים את הפלט ומבקשים תיקונים.

## שתי רמות של סוכנים

| | Development-time agent | Runtime agents |
|---|---|---|
| מי | Claude Code / Gemini CLI / Antigravity | Orchestrator, Research, Product, Developer, QA |
| מה עושה | כותב ומשנה את הקוד של הפרויקט | רצים בתוך האפליקציה ובונים את הסטארטאפ |
| מודל | של הכלי שבחרתם | Gemini (free tier) |
| מתי רץ | בזמן הפיתוח | בכל פעם שמריצים `python main.py` |

## הכנה לפני הסדנה (10 דקות)

1. **Python 3.11+** ו-**Node.js 18+** מותקנים.
2. **מפתח Gemini API בחינם:** https://aistudio.google.com/apikey
3. **סוכן קוד**, אחד מאלה:
   - **Claude Code:** דורש מנוי Claude בתשלום (Pro ומעלה).
   - **Gemini CLI עם מפתח API:** `npm install -g @google/gemini-cli`, ואז מגדירים את המפתח: `export GEMINI_API_KEY=...` ב-Mac/Linux, או `setx GEMINI_API_KEY ...` ב-Windows (ופותחים חלון חדש).
     ההתחברות החינמית עם חשבון Google הופסקה ב-18.6.2026, אבל עם מפתח API חינמי זה עדיין עובד במכסה יומית מוגבלת.
     מומלץ מפתח נפרד (פרויקט נפרד ב-AI Studio) לסוכן הקוד ולאפליקציה, כדי שלא יחלקו מכסה.
   - **Antigravity CLI** של Google: יש תוכנית חינמית עם מכסה נמוכה.
4. בתיקיית הפרויקט, **לפני** שמפעילים את סוכן הקוד:

   Mac / Linux:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env      # והדביקו את המפתח
   ```

   Windows (cmd או PowerShell):
   ```bat
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env    # והדביקו את המפתח
   ```

   בשורת הפקודה אמור להופיע `(.venv)`. רק אז מפעילים את סוכן הקוד (`claude` או `gemini`) מאותו חלון, כדי שהוא ירוץ בתוך הסביבה.

5. **בדיקה:** בסוכן הקוד כותבים `what are your instructions`. בתשובה צריכים להופיע הכללים מ-AGENTS.md. אם לא, הוא לא נפתח מתיקיית הפרויקט.

## מבנה הערכה

```
AGENTS.md            מסמך הארכיטקטורה שסוכן הקוד קורא (CLAUDE.md ו-GEMINI.md מפנים אליו)
prompts/prompts.md   כל ההנחיות של הסדנה, אותו נוסח כמו במצגת ובחוברת
exercises/           קבצים לתרגיל 6 (trace לדוגמה), וקובץ גיבוי לתרגיל 2
prompts/debugging.md איך מדווחים על באג לסוכן קוד
ideas.md             רעיונות לסטארטאפים להרצה
visualizer/          ויזואליזציה של הסוכנים בפעולה: דמו, או טעינה של trace.jsonl מריצה שלכם
```

## איך עובדים עם ההנחיות

כל הנחיה בנויה באותו מבנה: **מטרה → דרישות → חוזה (מה נכנס, מה יוצא) → קריטריון קבלה → "תראה לי תוכנית קודם".**
לא מעתיקים קוד. מעתיקים דרישות, קוראים את התוכנית שהסוכן מציע, ומאשרים או מתקנים.
