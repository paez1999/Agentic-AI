"""Streamlit UI for the Supply Chain multi-agent PoC."""

from __future__ import annotations

import pandas as pd
import pydeck as pdk
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from src.data.reference_locations import (
    COMPANY_KEY_PORTS,
    COMPANY_LOGISTIC_HUBS,
    DISASTER_SCENARIOS,
    IMPORTANT_PRODUCTS,
)
from src.reporting.formatter import format_final_markdown_report
from src.tasks.definitions import FlowInput, run_sequential_flow


def _render_agent_1(data: dict) -> None:
    st.subheader("Agente 1 - Monitoreo continuo de 5 puertos")
    summary = data.get("summary", {})
    ports = data.get("ports", [])
    c1, c2, c3 = st.columns(3)
    c1.metric("Puertos monitoreados", summary.get("scan_count", 0))
    c2.metric("Puertos en alto riesgo", len(summary.get("high_risk_ports", [])))
    c3.metric("Score promedio red", summary.get("avg_risk_score", 0))

    ports_df = pd.DataFrame(
        [
            {
                "Puerto": p.get("location"),
                "Severidad": p.get("severity"),
                "Score geopolítico": p.get("geopolitical_risk_score"),
                "Demora estimada (días)": p.get("expected_delay_days"),
                "Señales noticias": p.get("news_signal_count"),
                "Evento simulado": p.get("simulated_event") or "-",
            }
            for p in ports
        ]
    )
    st.dataframe(ports_df, use_container_width=True, hide_index=True)
    if not ports_df.empty:
        st.bar_chart(ports_df.set_index("Puerto")[["Score geopolítico"]])

    articles = []
    for p in ports:
        for a in p.get("geopolitical_articles", [])[:2]:
            articles.append({"Puerto": p.get("location"), "Titular": a.get("title"), "Fuente": a.get("domain")})
    st.write("**Muestra de noticias geopolíticas encontradas:**")
    if articles:
        st.dataframe(pd.DataFrame(articles), use_container_width=True, hide_index=True)
    else:
        st.info("No se detectaron noticias geopolíticas relevantes en esta ejecución.")


def _render_agent_2(data: dict) -> None:
    st.subheader("Agente 2 - Inventario por hubs logísticos (estático)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Stock (días)", data.get("stock_days_remaining", "-"))
    col2.metric("Unidades actuales", data.get("current_units", "-"))
    col3.metric("Uso diario promedio", data.get("average_daily_usage", "-"))
    st.progress(
        min(100, int(data.get("stock_days_remaining", 0) * 10)),
        text=f'Nivel de riesgo: {data.get("risk_level", "unknown")}',
    )
    hub_df = pd.DataFrame(data.get("hub_inventory", []))
    if not hub_df.empty:
        st.dataframe(hub_df, use_container_width=True, hide_index=True)


def _render_agent_3(data: dict, proposal_index: int = 0) -> None:
    st.subheader("Agente 3 - Generación de rutas posibles de envío")
    proposals = data.get("proposals", [])
    if not proposals:
        st.warning("No hay propuestas de ruta disponibles.")
        return
    proposal = proposals[min(proposal_index, len(proposals) - 1)]
    context_df = pd.DataFrame(
        [
            {"Contexto": "Severidad", "Valor": proposal.get("online_context_used", {}).get("severity", "-")},
            {
                "Contexto": "Demora base (días)",
                "Valor": proposal.get("online_context_used", {}).get("expected_delay_days", 0),
            },
            {
                "Contexto": "Señales geopolíticas",
                "Valor": proposal.get("online_context_used", {}).get("news_signal_count", 0),
            },
            {
                "Contexto": "Score geopolítico",
                "Valor": proposal.get("online_context_used", {}).get("geopolitical_risk_score", 0),
            },
        ]
    )
    st.dataframe(context_df, use_container_width=True, hide_index=True)
    st.write("**Opciones propuestas:**")
    options_df = pd.DataFrame(proposal.get("options", []))
    st.dataframe(options_df, use_container_width=True)

    st.write("**Visualización gráfica de rutas (Agente 3):**")
    if not options_df.empty:
        cost_chart = options_df.set_index("name")[["estimated_cost_usd"]]
        eta_chart = options_df.set_index("name")[["eta_days"]]
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Comparativo de costo por ruta")
            st.bar_chart(cost_chart)
        with c2:
            st.caption("Comparativo de ETA por ruta")
            st.bar_chart(eta_chart)

    st.write("**Mapa de recorrido de la mercancía:**")
    route_map = proposal.get("route_map", {})
    origin_point = route_map.get("origin_point", {})
    destination_point = route_map.get("destination_point", {})
    route_paths = route_map.get("paths", [])
    if not origin_point or not destination_point or not route_paths:
        st.warning("Agente 3 no generó información cartográfica para las rutas.")
        return

    points_df = pd.DataFrame(
        [
            {"point": "Origen", "lat": origin_point.get("lat"), "lon": origin_point.get("lon")},
            {"point": "Destino", "lat": destination_point.get("lat"), "lon": destination_point.get("lon")},
        ]
    )
    routes_df = pd.DataFrame(
        [
            {"route": route["route_name"], "path": route["path"], "color": route["color"]}
            for route in route_paths
        ]
    )

    center_lat = points_df["lat"].mean()
    center_lon = points_df["lon"].mean()
    deck = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=2.2, pitch=25),
        layers=[
            pdk.Layer(
                "PathLayer",
                data=routes_df,
                get_path="path",
                get_color="color",
                width_scale=8,
                width_min_pixels=3,
                pickable=True,
            ),
            pdk.Layer(
                "ScatterplotLayer",
                data=points_df,
                get_position="[lon, lat]",
                get_radius=120000,
                get_color=[200, 30, 0],
                pickable=True,
            ),
        ],
        tooltip={"text": "{route}"},
    )
    st.pydeck_chart(deck, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Supply Chain AI PoC", layout="wide")
    st.title("Supply Chain AI PoC - Panel de Agentes")
    st.caption("Monitoreo continuo cada 15 segundos sobre la red corporativa de 5 puertos clave.")

    params = st.query_params
    active_disaster_name = params.get("active_disaster", "Sin simulación")
    if active_disaster_name not in DISASTER_SCENARIOS:
        active_disaster_name = "Sin simulación"
    auto_refresh_enabled = active_disaster_name == "Sin simulación"
    if auto_refresh_enabled:
        st_autorefresh(interval=15_000, key="network_monitor_refresh")

    with st.sidebar:
        st.header("Parámetros de red")
        st.write("**Puertos clave de la compañía (fijos):**")
        for port in COMPANY_KEY_PORTS:
            st.caption(f"- {port}")
        st.write("**Hubs logísticos (fijos):**")
        for hub in COMPANY_LOGISTIC_HUBS:
            st.caption(f"- {hub}")
        product_id = st.selectbox("Producto estratégico", IMPORTANT_PRODUCTS, index=0)

        default_disaster_index = list(DISASTER_SCENARIOS.keys()).index(active_disaster_name)
        disaster_name = st.selectbox(
            "Escenario de desastre regional",
            list(DISASTER_SCENARIOS.keys()),
            index=default_disaster_index,
        )
        simulate_clicked = st.button("Simular desastre y reaccionar", type="primary", use_container_width=True)
        stop_disaster_clicked = st.button("Detener desastre activo", use_container_width=True)

    if simulate_clicked:
        params["active_disaster"] = disaster_name
        active_disaster_name = disaster_name
    if stop_disaster_clicked:
        params["active_disaster"] = "Sin simulación"
        active_disaster_name = "Sin simulación"

    active_disaster = DISASTER_SCENARIOS[active_disaster_name]
    if active_disaster.get("enabled"):
        st.warning(f'Evento activo: {active_disaster.get("event")}')
    else:
        st.info("Monitoreo continuo en modo normal (sin desastre activo).")

    # Continuous monitoring on every run (including 15s auto refresh)
    if True:
        flow_input = FlowInput(
            product_id=product_id,
            key_ports=COMPANY_KEY_PORTS,
            logistic_hubs=COMPANY_LOGISTIC_HUBS,
            simulated_disaster=active_disaster,
        )
        st.session_state["flow_result"] = run_sequential_flow(flow_input)
        st.session_state["selected_option"] = None

    flow_result = st.session_state.get("flow_result")
    if not flow_result:
        st.info("Presiona 'Ejecutar análisis' para generar resultados.")
        return

    col1, col2 = st.columns(2)
    with col1:
        _render_agent_1(flow_result["task_1_monitor_output"])
    with col2:
        _render_agent_2(flow_result["task_2_inventory_output"]["inventory_status"] | {"hub_inventory": flow_result["task_2_inventory_output"].get("hub_inventory", [])})

    st.divider()
    proposal_count = len(flow_result["task_3_route_output"].get("proposals", []))
    selected_proposal = 0
    if proposal_count > 1:
        selected_proposal = st.selectbox(
            "Selecciona propuesta de ruta a visualizar",
            options=list(range(proposal_count)),
            format_func=lambda i: f'Propuesta {i + 1}',
        )
    _render_agent_3(flow_result["task_3_route_output"], proposal_index=selected_proposal)

    st.divider()
    st.subheader("Decisión humana (Human-in-the-Loop)")
    cta1, cta2 = st.columns(2)
    with cta1:
        if st.button("Autorizar Opción A", use_container_width=True):
            st.session_state["selected_option"] = "A"
    with cta2:
        if st.button("Autorizar Opción B", use_container_width=True):
            st.session_state["selected_option"] = "B"

    selected = st.session_state.get("selected_option")
    if selected:
        st.success(f"Decisión registrada: Opción {selected}")

    st.divider()
    st.subheader("Reporte final (Markdown)")
    st.markdown(format_final_markdown_report(flow_result))


if __name__ == "__main__":
    main()
