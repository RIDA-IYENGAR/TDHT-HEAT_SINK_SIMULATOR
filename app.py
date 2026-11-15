import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import sample_colorscale
from plotly.subplots import make_subplots

st.set_page_config(page_title="TDHT Heat Sink Virtual Lab", page_icon="🌡️", layout="wide")

MATERIALS = {
    "Aluminium": 205.0,
    "Copper": 385.0,
    "Stainless steel": 16.0,
}

def fin_solution(k, h, width, thickness, length, Tb, Tinf, n=301):
    """Analytical 1-D straight-fin solution with convection from sides and tip."""
    Ac = width * thickness
    P = 2 * (width + thickness)
    Af = P * length + Ac
    m = np.sqrt(h * P / (k * Ac))
    beta = h / (m * k)
    x = np.linspace(0, length, n)
    theta_b = Tb - Tinf
    den = np.cosh(m * length) + beta * np.sinh(m * length)
    T = Tinf + theta_b * (
        np.cosh(m * (length - x)) + beta * np.sinh(m * (length - x))
    ) / den
    q = np.sqrt(h * P * k * Ac) * theta_b * (
        np.sinh(m * length) + beta * np.cosh(m * length)
    ) / den
    eta = q / (h * Af * theta_b)
    effectiveness = q / (h * Ac * theta_b)
    return x, T, q, eta, effectiveness, Ac, P, Af

def heat_sink_figure(x, T, Tb, Tinf, width_mm=30):
    """Create a visual fin with temperature-coloured segments and animated heat markers."""
    nseg = 45
    idx = np.linspace(0, len(x)-1, nseg+1).astype(int)
    xx = x[idx] * 1000
    tt = T[idx]
    fig = go.Figure()
    # fin segments coloured by temperature
    for i in range(nseg):
        # Plotly line.color needs a CSS colour string; convert temperature to a Turbo colour.
        fraction = float(np.clip((tt[i] - Tinf) / max(Tb - Tinf, 1e-9), 0.0, 1.0))
        segment_color = sample_colorscale("Turbo", [fraction])[0]
        fig.add_trace(go.Scatter(
            x=[xx[i], xx[i+1]], y=[0, 0],
            mode="lines",
            line=dict(color=segment_color, width=30),
            showlegend=False, hovertemplate=f"Position: {xx[i]:.1f} mm<br>Temperature: {tt[i]:.1f} °C<extra></extra>"
        ))
    # Base block
    fig.add_shape(type="rect", x0=-8, x1=0, y0=-0.32, y1=0.32,
                  fillcolor="#9b5b37", line=dict(color="#6f3e28", width=2))
    # moving heat particles, phase controlled by Plotly animation
    frames=[]
    for phase in range(12):
        px=[]; py=[]; pcolor=[]
        for j in range(9):
            f=((phase/12 + j/9) % 1)
            px.append(f*xx[-1])
            py.append(0.22 + 0.07*np.sin((f*4+j)*2))
            pcolor.append(float(np.interp(f, x/length_safe(x), T)))
        frames.append(go.Frame(data=[go.Scatter(
            x=px,y=py,mode="markers",
            marker=dict(size=9,color=pcolor,colorscale="Turbo",cmin=Tinf,cmax=Tb,
                        line=dict(width=1,color="white")),
            showlegend=False)], name=str(phase), traces=[nseg]))
    fig.frames=frames
    # initial particle trace
    fig.add_trace(go.Scatter(x=[],y=[],mode="markers",
        marker=dict(size=9,color=[],colorscale="Turbo",cmin=Tinf,cmax=Tb),
        showlegend=False,hoverinfo="skip"))
    fig.update_layout(
        height=340, margin=dict(l=20,r=20,t=20,b=35),
        xaxis=dict(title="Distance from heated base (mm)",range=[-10,xx[-1]+5],showgrid=False),
        yaxis=dict(range=[-0.55,0.65],visible=False),
        plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
        updatemenus=[dict(type="buttons",showactive=False,x=1,y=1.18,
          buttons=[dict(label="▶ Animate heat flow",method="animate",
            args=[None,{"frame":{"duration":110,"redraw":False},"fromcurrent":True,
                         "transition":{"duration":80},"mode":"immediate"}]),
                   dict(label="Ⅱ Pause",method="animate",
                    args=[[None],{"frame":{"duration":0,"redraw":False},"mode":"immediate"}])])]
    )
    fig.add_annotation(x=xx[-1]*0.5,y=-0.43,text="Heat conducts from base → tip; fin surface loses heat by convection",
                       showarrow=False,font=dict(size=11))
    return fig

def length_safe(x):
    return x[-1] if x[-1] else 1.0

st.title("🌡️ TDHT Virtual Laboratory: Heat Sink Fin")
st.caption("Interactive steady-state heat conduction and convection simulator | Rectangular fin with convective tip")

with st.sidebar:
    st.header("Simulation controls")
    material=st.selectbox("Fin material",list(MATERIALS.keys()))
    k=MATERIALS[material]
    L_mm=st.slider("Fin length (mm)",10,120,50,5)
    width_mm=st.slider("Fin width (mm)",10,60,30,5)
    thickness_mm=st.slider("Fin thickness (mm)",0.5,5.0,2.0,0.25)
    Tb=st.slider("Base temperature (°C)",40,150,80,5)
    Tinf=st.slider("Ambient temperature (°C)",10,40,25,1)
    cooling=st.selectbox("Cooling condition",["Natural convection","Forced air","High airflow"])
    h={"Natural convection":25.0,"Forced air":80.0,"High airflow":140.0}[cooling]
    st.caption(f"Convection coefficient h = {h:.0f} W/m²K")
    st.divider()
    st.caption("Model assumptions: steady state, 1-D conduction, constant properties, uniform h, negligible radiation and perfect base contact.")

if Tb <= Tinf:
    st.error("Base temperature must be higher than ambient temperature.")
    st.stop()

L=L_mm/1000
w=width_mm/1000
t=thickness_mm/1000
x,T,q,eta,effectiveness,Ac,P,Af=fin_solution(k,h,w,t,L,Tb,Tinf)
tip=float(T[-1])

c1,c2,c3,c4=st.columns(4)
c1.metric("Heat transfer per fin",f"{q:.3f} W")
c2.metric("Fin efficiency",f"{eta*100:.1f}%")
c3.metric("Tip temperature",f"{tip:.1f} °C")
c4.metric("Fin effectiveness",f"{effectiveness:.2f}")

st.subheader("1. Live thermal model")
st.plotly_chart(heat_sink_figure(x,T,Tb,Tinf),use_container_width=True,config={"displayModeBar":False})

left,right=st.columns(2)
with left:
    st.subheader("2. Temperature distribution")
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=x*1000,y=T,mode="lines",name="Fin temperature",
                             line=dict(color="#e87535",width=3),
                             hovertemplate="x=%{x:.1f} mm<br>T=%{y:.2f} °C<extra></extra>"))
    fig.add_hline(y=Tinf,line_dash="dash",line_color="#2785b8",annotation_text="Ambient")
    fig.update_layout(height=340,xaxis_title="Distance from base (mm)",yaxis_title="Temperature (°C)",
                      margin=dict(l=10,r=10,t=15,b=10))
    st.plotly_chart(fig,use_container_width=True)
with right:
    st.subheader("3. Convective heat flux")
    qflux=h*(T-Tinf)
    fig2=go.Figure(go.Scatter(x=x*1000,y=qflux,mode="lines",fill="tozeroy",
                              line=dict(color="#2697a8",width=3),name="Surface heat flux"))
    fig2.update_layout(height=340,xaxis_title="Distance from base (mm)",
                       yaxis_title="Local convective heat flux (W/m²)",
                       margin=dict(l=10,r=10,t=15,b=10))
    st.plotly_chart(fig2,use_container_width=True)

st.subheader("4. Material comparison")
rows=[]
for mat, kval in MATERIALS.items():
    _,_,qmat,emat,effmat,*_=fin_solution(kval,h,w,t,L,Tb,Tinf)
    rows.append({"Material":mat,"Thermal conductivity (W/m·K)":kval,
                 "Heat transfer (W)":qmat,"Fin efficiency (%)":emat*100,
                 "Effectiveness":effmat})
df=pd.DataFrame(rows)
st.dataframe(df.style.format({"Thermal conductivity (W/m·K)":"{:.1f}",
                               "Heat transfer (W)":"{:.3f}",
                               "Fin efficiency (%)":"{:.1f}",
                               "Effectiveness":"{:.2f}"}),use_container_width=True,hide_index=True)
bar=go.Figure(go.Bar(x=df["Material"],y=df["Heat transfer (W)"],marker_color=["#3696bb","#d68a3b","#7a8a99"]))
bar.update_layout(height=280,yaxis_title="Heat transfer (W)",margin=dict(l=10,r=10,t=10,b=10))
st.plotly_chart(bar,use_container_width=True)

st.subheader("5. Fin-length design study")
lengths=np.linspace(10,120,45)
study=[]
for lm in lengths:
    _,_,qq,ee,_,*_=fin_solution(k,h,w,t,lm/1000,Tb,Tinf,n=151)
    study.append((lm,qq,ee*100))
study_df=pd.DataFrame(study,columns=["Length (mm)","Heat transfer (W)","Efficiency (%)"])
fig3=make_subplots(specs=[[{"secondary_y":True}]])
fig3.add_trace(go.Scatter(x=study_df["Length (mm)"],y=study_df["Heat transfer (W)"],
                          name="Heat transfer",line=dict(color="#d97732",width=3)),secondary_y=False)
fig3.add_trace(go.Scatter(x=study_df["Length (mm)"],y=study_df["Efficiency (%)"],
                          name="Efficiency",line=dict(color="#2585a4",width=3,dash="dash")),secondary_y=True)
fig3.update_xaxes(title_text="Fin length (mm)")
fig3.update_yaxes(title_text="Heat transfer (W)",secondary_y=False)
fig3.update_yaxes(title_text="Efficiency (%)",secondary_y=True)
fig3.update_layout(height=350,margin=dict(l=10,r=10,t=10,b=10))
st.plotly_chart(fig3,use_container_width=True)

st.info(f"**Engineering interpretation:** With {material.lower()} and {cooling.lower()}, the fin transfers {q:.3f} W. The temperature falls from {Tb:.1f} °C at the base to {tip:.1f} °C at the tip. Increasing airflow increases h and strengthens convection; increasing thermal conductivity generally keeps the fin temperature more uniform.")

st.caption("Educational model. The animated particles illustrate heat-flow direction; the calculated temperature field is steady-state, not a transient CFD solution.")
