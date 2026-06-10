.PHONY: all live historical data models film report visuals verify clean

all: live historical data models film report visuals verify

live:
	python3 src/fetch_live_data.py
	python3 src/fetch_additional_sources.py

historical:
	python3 src/fetch_historical_data.py

data:
	python3 src/build_live_datasets.py
	python3 src/build_historical_dataset.py

models:
	python3 src/run_modeling_and_comps.py

film:
	python3 src/import_film_archive.py

report:
	python3 src/generate_latex_report.py

visuals:
	python3 src/create_shareable_graphic.py

verify:
	python3 -m py_compile src/*.py
	test -s report/final_report.pdf
	test -s report/report.tex
	test -s big_board.md
	test -s figures/shareable_mock_draft_16x9.png
	test -s figures/shareable_mock_draft_story_deck.pdf

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	rm -f report/report.pdf report/report.aux report/report.log report/report.out report/report.toc
