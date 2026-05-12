.PHONY: setup run app dashboard decision check docker

setup:
	python -m pip install -U pip
	python -m pip install -r requirements.txt

run:
	python run.py

app:
	streamlit run app.py

dashboard:
	streamlit run dashboard.py

decision:
	streamlit run src/decision_visualizer.py --server.port 8502

check:
	python -m compileall .

docker:
	docker compose -f docker/docker-compose.yml up --build
