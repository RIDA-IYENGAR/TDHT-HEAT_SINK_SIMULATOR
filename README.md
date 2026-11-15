# TDHT Heat Sink Fin Virtual Laboratory

## Run locally (Mac/Linux)
```bash
cd TDHT_HeatSink_Simulator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Open the local URL printed in Terminal (usually http://localhost:8501).

## Model
Steady-state 1-D straight rectangular fin with convective side surfaces and convective tip. The analytical temperature distribution is recalculated for every slider selection. The app visualizes heat-flow direction, temperature, convective heat flux, material comparison and fin-length trade-offs.

## Assumptions
Constant properties, uniform convection coefficient, negligible radiation, no internal heat generation, perfect base contact and one-dimensional conduction.
