doc:
	mkdir -p docs
	for m in $$(ls modules/*.py); do ./generate_doc.py $$m docs/$$(basename $$m .py).md; done

clean:
	rm -rf docs

.PHONY: doc clean
