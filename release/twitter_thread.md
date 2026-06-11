# Release thread, 2026 NBA Draft AI Big Board (final)

Repo (both runs), https://github.com/arcAman07/nba-draft-2026-ai-big-board

Seven tweets. All attachment images are in release/images/, named by tweet number. Every tweet verified under 280 characters.

---

## Tweet 1 (opener)

Attach, release/images/tweet1_social_board.png

I genuinely believe the next frontier for these models is prediction. So I turned Claude's new Fable model into an NBA front office for a day. A full 2026 draft big board built completely on its own. Footage, models, comps, team needs, a paper. Codex got the same prompt 🧵

## Tweet 2

No attachment

Zero hints from me, and they split at No. 1. Codex went Dybantsa, Fable went Boozer. The reason is structural. Codex fed the market's own ranking into its model and that one feature became 16x more important than anything else. Fable deliberately left it out to isolate talent.

## Tweet 3

Attach, release/images/tweet3_feature_importance.png

How Fable evaluates talent surprised me. Its model says the biggest factor in the entire draft is simply being young. Then college BPM, then passing. Height came out slightly negative. And it learned that missing data is itself a red flag, players without stats bust more often.

## Tweet 4

Attach, release/images/tweet4_pred_vs_consensus.png

It gets weirder. Wingspan says almost nothing about how good you become but a lot about whether you bust. Defensive college stars age better than offensive ones at the same production. And draft position predicts busts well but ranks lottery talent badly, 0.145 vs 0.256 Spearman.

## Tweet 5

Attach, release/images/tweet5_comp_cohorts.png

The most human thing it did was overrule itself. Its model ranked Nate Ament 25th, but his comp cohort (Barnes, Deng, Tatum) says models miss teenage 6'10 shot creators, so Fable kept him 8th and wrote down why. With Quaintance it priced the ACL, not the 4-game sample.

## Tweet 6

Attach, release/images/tweet6_boozer_frame.jpg

And my favorite moments. Fable refused to grade two prospects' jumpers because it never caught a clean rep in its 12,000 film stills. Codex listed Jarrett Culver as both Dybantsa's floor and his median outcome. Both found the same Wayback workaround when stats.nba.com died.

## Tweet 7 (closer)

No attachment, the link unfurls

Both papers (32 and 59 pages), both boards, all the code and logs are public. The draft is in two weeks, then we know which model was right.

https://github.com/arcAman07/nba-draft-2026-ai-big-board

---

## Single-tweet version (if you skip the thread)

Attach, release/images/tweet1_social_board.png

I think prediction problems are the next real test for frontier models. So Claude Fable 5 and Codex GPT 5.5 each built a 2026 NBA draft big board completely on their own, footage analysis included. Codex took Dybantsa at 1. Fable argued for Boozer.

https://github.com/arcAman07/nba-draft-2026-ai-big-board
