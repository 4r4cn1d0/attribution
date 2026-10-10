"""Make the ACL Rolling Review version of the note from the arXiv source.

    python3 make_arr.py            # reads ../arxiv/main.tex, writes main.tex here

The content stays the arXiv text. Only what ARR requires changes: the official ACL
template in review mode (anonymous, line numbers), a dedicated Limitations section after
the conclusion with no new results, an optional "Ethical considerations" section with
the AI-assistance disclosure, no repository link (anonymity), double-column appendices,
and the screening log moved to an appendix. Every replaced block must be found exactly
once, or the script stops.
"""
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "arxiv" / "main.tex"

PREAMBLE = r"""\pdfoutput=1
\documentclass[11pt]{article}
\usepackage[review]{acl}
\usepackage{times}
\usepackage{latexsym}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{microtype}
\usepackage{inconsolata}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{xurl}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{mathtools}
\usepackage[capitalize,noabbrev]{cleveref}
\usepackage{array}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcommand{\ph}[1]{#1}
\newcommand{\Uo}{U_0}
\newcommand{\Uft}{U_{\mathrm{ft}}}
\newcommand{\Ehb}{E_{\mathrm{HB}}}
\raggedbottom

\title{Same Recipe, Different Fate:\\
The Training Recipe's Effect on Safety Erosion from Benign Fine-Tuning Depends on the Model Family}
\author{Anonymous ACL submission}

"""

SECTION6 = r"""\section{What the measure means}
\label{sec:screened}

\paragraph{What $U$ tracks.} $U$ is a broad policy label. After fine-tuning, the
probability of an Unsafe label given no refusal is 0.91--0.94, so $U$ mostly
tracks lost refusal. Under hard categories only, OLMo's $E$ is about 28 pp.
Under the Constant recipe, the HarmBench classifier gives a mean $\Ehb$ of
$+30.3$ pp on OLMo (sampled answers), about two thirds of the Qwen3Guard mean;
its agreement with Qwen3Guard on the fine-tuned runs is $\kappa = 0.65$--$0.71$.

\paragraph{A blind human read.} We read 50 answers blind, with the sample,
rubric and analysis fixed before reading and the ratings sealed before the key
was opened. Of 39 rated answers labelled Unsafe, 34 (0.87, 95\% interval
0.73--0.96) went along with the request, but only 13 (0.33, 0.19--0.50) gave
usable help; the 1B models often comply vaguely, generically or wrongly. All 10
Safe-labelled controls were refusals or deflections. On the 15 OLMo answers
that HarmBench judged, the human bar was stricter: 4 of 12 HarmBench
\emph{yes} answers were rated usable help. So $U$ measures lost refusal well,
and usable harm is a smaller share.

JUDGE_WORDING

\paragraph{What we screened.} \Cref{app:screening} lists every setting we ran,
in time order, including runs that did not enter the tables. Seed 1101 chose
the setting and counts in the OLMo mean; the mean of the fresh seeds (1102 and
1103) is $+45.9$ pp.

"""

LIMITATIONS = r"""\section*{Limitations}

\begin{itemize}
  \item \textbf{Scope.} Every claim holds only for these models (three
        instruct families at 1B, and Qwen2.5-7B, OLMo-2-7B and Llama-3.1-8B
        under the constant-rate recipe only), Dolly and the two fiction
        datasets (on OLMo-2-1B only), LoRA fine-tuning, these recipes, the 200
        development harm prompts and these judges. No result is confirmed on
        held-out prompts.
  \item \textbf{Choices made after seeing results.} We fixed the 20--55 pp
        window for partial erosion after the three Qwen results, with no
        written reason for 20 and 55. Seed 1101 chose the setting and counts in
        the OLMo mean. We wrote the exact family-by-recipe test after 11 of its
        12 values were known. Rules or predictions written before their runs
        cover the Scheduled recipe, the token-mean recipe, rank 16 and the
        fiction study, and the human read's analysis was fixed before reading;
        the other comparisons are descriptive (\cref{tab:claims}).
  \item \textbf{Fiction study.} One family, one recipe and 16 books. The
        fiction-trained models also refused more benign prompts and lost ARC
        accuracy, so their lower erosion may come from weaker instruction
        following. The margins are wide (about a third of Dolly's erosion), so
        ``no difference larger than the margin'' is a weak equivalence claim.
  \item \textbf{Few seeds.} The between-seed variance rests on 2 df: the
        sample SD's 90\% range is 0.23--1.73 times the true SD. The OLMo band
        covers evaluation noise only. The Qwen results, the 7--8B rows and the
        variant rows with rank 16 or half the learning rate rest on one or two
        seeds, and the family-by-recipe test has about 5 df. The family-by-recipe
        test is at 1B only.
  \item \textbf{What the judge measures.} $U$ is a broad policy label that
        mostly tracks lost refusal (\S\ref{sec:screened}), and usable harm is a
        smaller share. HarmBench did not judge every unit, and Granite judged
        greedy answers only.
  \item \textbf{Differences between families.} The families differ in chat
        template, tokeniser (so the same rows give different token counts),
        post-training pipeline and starting over-refusal. The Qwen runs, OLMo's
        Constant runs and the other runs used three engine identities
        (\cref{app:hashes}). We claim no cause for the family difference.
  \item \textbf{Recipes.} The Constant recipe is not standard practice. The
        token-mean recipe separates the loss weighting from the schedule, but
        not the schedule's warmup from its decay, which also halves the mean
        learning rate.
  \item \textbf{Human read.} One reader, who designed parts of the study,
        rated 50 answers. There is no second rater, and the groups are too
        small to compare.
  \item \textbf{ARC.} The ARC check is uninformative at 1B.
\end{itemize}

\section*{Ethical considerations}

This paper measures how fine-tuning on benign data erodes refusal in small open
models, so that practitioners can see that the model family and the training
recipe change the result. It proposes no attack, and the training data is a
public benign instruction dataset. The results could in principle help someone
choose a recipe that removes refusals; we judge this risk small, since the
effects concern 1B models trained on benign data, and the same knowledge helps
practitioners keep refusals. We release no harmful prompt or answer text, and
we use every model, dataset and judge for research, consistent with its licence
(\cref{app:artifacts}). An author read 50 model answers to harmful requests for
the blind human read, with the rubric in \cref{app:artifacts}; no other
annotators took part.

\paragraph{Use of AI assistants.} We used AI assistants (Claude, Anthropic)
extensively: to help design and pre-register the analyses, to write the
analysis and run-management code, to check every reported number against the
run records, and to draft and edit the text. The authors made every study
decision and take full responsibility for the content.

"""

SCREENING_APPENDIX_HEAD = r"""\section{Screening log}
\label{app:screening}

"""


def once(text, old, new):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"expected one match, found {n}: {old[:70]!r}")
    return text.replace(old, new)


def between(text, start, end):
    a = text.index(start)
    b = text.index(end, a)
    return a, b


def main():
    s = SRC.read_text()
    body = s[s.index(r"\begin{document}"):]

    # Title block: the ICML title and author block go; \maketitle comes in.
    a, b = between(body, r"\twocolumn[", r"\printAffiliationsAndNotice{}")
    b = body.index("\n", b) + 1
    body = body[:a] + "\\maketitle\n" + body[b:]

    # Table 2 is 21.7 pt too wide for the ACL text width: narrow its two fixed judge columns.
    body = once(body, r"\begin{tabular}{@{}l l c c C{2.2cm} c c C{2.3cm}@{}}",
                r"\begin{tabular}{@{}l l c c C{1.8cm} c c C{1.9cm}@{}}")

    # Release: no repository link in an anonymous submission.
    body = once(body, "(no prompt or answer text), the analysis scripts and the figure data at\n"
                      r"\url{https://github.com/4r4cn1d0/same-recipe-different-fate}.",
                "(no prompt or answer text), the analysis scripts and the figure data with\n"
                "the final version.")
    body = once(body, r"\paragraph{Release.} We release", r"\paragraph{Release.} We will release")

    # Section 6: results stay in the main text; the log goes to an appendix.
    a, b = between(body, r"\section{What we screened, and limits}", r"\section{Related work}")
    old6 = body[a:b]
    la, lb = between(old6, r"\paragraph{Screening log.}", r"\paragraph{Disclosures.}")
    screening = old6[la:lb].replace(r"\paragraph{Screening log.} ", "", 1)
    ja = old6.index(r"\paragraph{Judge wording.}")
    judge = old6[ja:].rstrip() + "\n"
    body = body[:a] + SECTION6.replace("JUDGE_WORDING", judge) + body[b:]

    # Impact statement -> Limitations + Ethical considerations, before the references.
    a, b = between(body, r"\section*{Impact Statement}", r"\bibliography{references}")
    body = body[:a] + LIMITATIONS + body[b:]
    body = once(body, "\\bibliographystyle{icml2026}\n", "")      # acl.sty sets acl_natbib itself

    # Appendices: double-column (ARR), wide tables as table*, the screening log added.
    body = once(body, "\\newpage\n\\appendix\n\\onecolumn\n", "\\appendix\n")
    head, tail = body.split("\\appendix\n", 1)
    tail = tail.replace("\\newpage\n", "")
    tail = tail.replace("\\begin{table}[h]", "\\begin{table*}[t]").replace("\\begin{table}[!htbp]", "\\begin{table*}[t]")
    tail = tail.replace("\\end{table}", "\\end{table*}")
    tail = tail.replace("L{4.3cm}L{12.4cm}", "L{3.9cm}L{11.6cm}")
    tail = tail.replace(r"\end{document}", SCREENING_APPENDIX_HEAD + screening.strip() + "\n\n" + r"\end{document}")
    body = head + "\\appendix\n" + tail

    out = PREAMBLE + body
    for bad in ("icml", r"\ph{", "4r4cn1d0", "Impact Statement"):
        hits = [ln for ln in out.split("\n") if bad in ln and not ln.lstrip().startswith("%")]
        if hits:
            raise SystemExit(f"left in the ARR text: {bad!r}: {hits[0][:80]}")
    (HERE / "main.tex").write_text(out)
    print("wrote", HERE / "main.tex")


if __name__ == "__main__":
    main()
