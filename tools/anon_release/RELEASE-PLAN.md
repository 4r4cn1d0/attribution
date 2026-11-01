# Anonymous code release: the user's route (decided 2026-10-30)

The user's decision (GI VIII chat, verbatim: "New private repo"): the main study's anonymous code goes to a **new
private repo under the user's own GitHub account**, served to reviewers through a **new** anonymous.4open.science
mirror, at submission time. The existing staging repo and its auto-publishing mirror are not used for this export.

## At submission time
1. The lead runs `anon_export.py` at that day's commit into a new folder outside the project, then `anon_check.py`
   (must exit 0), then makes one commit in that folder with a neutral author (`Anonymous <anonymous@example.com>`).
2. The user creates the new private repo (a neutral name, no README, no licence template) and pushes that folder to
   it (or tells the lead to push it).
3. The user opens anonymous.4open.science, signs in with GitHub, anonymizes the new repo: terms to hide (name,
   handle, email, repo owner), auto-update OFF, expiry after the review period.
4. The anonymous URL goes into the paper. Before that, the lead re-reads the mirror page for any identifying text.

## Open
- Licence (MIT or Apache-2.0 are usual): the user decides; EXPORT-README says it is to be added.
