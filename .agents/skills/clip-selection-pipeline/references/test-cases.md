# Clip Selection Pipeline Test Cases

Use small text and timestamp fixtures only; do not add video fixtures yet.

| Case | Expected result |
|---|---|
| Strong Arabic hook | Valid high-scoring candidate with RTL-safe transcript |
| Iraqi Arabic hook | Meaning preserved; confidence reflects transcript evidence |
| English hook | Valid candidate with complete boundaries |
| Mixed Arabic and English | Valid language-aware transcript and subtitle grouping |
| Weak greeting | Rejected or heavily penalized |
| Delayed payoff | Retention penalty and trim recommendation |
| Incomplete context | Rejected unless context-rich boundary resolves it |
| Repeated idea | One candidate retained with duplicate rejection reason |
| Overlapping timestamps | Strict diversity rejects weaker overlap |
| Emotional, low-value moment | Emotion alone does not force selection |
| Useful, calm moment | Meaningful content can rank despite low energy |
| Silence at beginning | Opening penalty or boundary adjustment |
| Natural loop ending | Boundary variant can preserve loop |
| Incomplete ending | Candidate rejected or extended to payoff |
| Requested count exceeds strong candidates | Highest Potential returns fewer; Exact Count labels backups |
