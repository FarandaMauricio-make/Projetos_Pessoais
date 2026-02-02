import requests
import pandas as pd
import streamlit as st
import altair as alt
import datetime as dt

# 1. Criar mapa manual de dias da semana (evita bug de encoding no sábado)

dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]

# 2. Dados do Clima em Lavras - MG (Previsão Horária)

# Função cacheada para buscar previsão
@st.cache_data(ttl=3600)  # guarda os dados por 1 hora
def get_forecast():
    url_forecast = "http://api.open-meteo.com/v1/forecast"
    params_forecast = {
        "latitude": -21.245,
        "longitude": -45.000,
        "hourly": "temperature_2m,relativehumidity_2m,windspeed_10m"
    }
    response_forecast = requests.get(url_forecast, params=params_forecast)
    return response_forecast.json()

# Uso no app
data_forecast = get_forecast()

# Criando DataFrame da previsão horária
df_forecast = pd.DataFrame({
    "Tempo": data_forecast["hourly"]["time"],
    "Temperatura (°C)": data_forecast["hourly"]["temperature_2m"],
    "Umidade (%)": data_forecast["hourly"]["relativehumidity_2m"],
    "Vento (m/s)": data_forecast["hourly"]["windspeed_10m"]
})

df_forecast["Tempo"] = pd.to_datetime(df_forecast["Tempo"])  # Converter para datetime

# 3. Dados do Clima em Lavras - MG (Histórico Diário)

st.sidebar.header("📅 Filtro de período do histórico")

hoje = dt.date.today()
default_start = hoje - dt.timedelta(days=30)  # Últimos 30 dias como padrão
default_end = hoje

start_date = st.sidebar.date_input("Data inicial", default_start)
end_date = st.sidebar.date_input("Data final", default_end)

if start_date > end_date:
    st.sidebar.error(" ⚠️ A data de início deve ser anterior à data final.")
    df_historical = pd.DataFrame()
else:
    # Função cacheada para buscar dados históricos
    @st.cache_data(ttl=3600)  # guarda os dados por 1 hora
    def get_historical(start_date, end_date):
        url_historical = "http://archive-api.open-meteo.com/v1/archive"
        params_historical = {
            "latitude": -21.245,
            "longitude": -45.000,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum"
        }
        response_historical = requests.get(url_historical, params=params_historical)
        return response_historical.json()

    # Chama a função cacheada
    data_historical = get_historical(start_date, end_date)
    df_historical = pd.DataFrame(data_historical["daily"])

    # Criando DataFrame do histórico diário

    df_historical = pd.DataFrame({
        "Tempo": data_historical["daily"]["time"],
        "Temperatura Máxima diária (°C)": data_historical["daily"]["temperature_2m_max"],
        "Temperatura Mínima diária (°C)": data_historical["daily"]["temperature_2m_min"],
        "Precipitação (mm)": data_historical["daily"]["precipitation_sum"]
    })

    df_historical["Tempo"] = pd.to_datetime(df_historical["Tempo"])  # Converter para datetime

# 4. Função auxiliar para formatar eixo X com data + dia da semana

def eixo_x():
    return alt.X(
        "Tempo:T",
        axis=alt.Axis(
            labelExpr="timeFormat(datum.value, '%d/%m') + ' (' + ['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'][timeFormat(datum.value, '%w')] + ')'"
        )
    )

# 5. Streamlit Dashboard

st.title("🌦️ Dashboard do Clima em Lavras - MG")
st.markdown("Este painel mostra **previsão horária** e **histórico diário** de clima em Lavras - MG. Use as abas abaixo para navegar.")

# Storytelling introdutório
st.info(f"📖 Entre {start_date.strftime('%d/%m/%Y')} e {end_date.strftime('%d/%m/%Y')}, os dados revelam como o clima de Lavras se comportou. Vamos explorar a história que o céu contou nesse período.")

tab1, tab2 = st.tabs(["📅 Previsão Horária (Mês Atual)", "📆 Histórico Diário"])

with tab1:
    st.header("📈 Temperatura ao longo do tempo")
    chart_temp = (
        alt.Chart(df_forecast)
        .mark_line(color="red")
        .encode(
            x=eixo_x(),
            y="Temperatura (°C):Q",
            tooltip=["Tempo", "Temperatura (°C)"]
        )
        .properties(width=700, height=400)
    )
    st.altair_chart(chart_temp, use_container_width=True)

    st.header("📊 Temperatura, Umidade e Vento")
    opcoes_forecast = st.multiselect(
        "Selecione variáveis para visualizar:",
        ["Temperatura (°C)", "Umidade (%)", "Vento (m/s)"],
        default=["Temperatura (°C)", "Umidade (%)", "Vento (m/s)"]
    )

    # Transformar para formato longo
    df_forecast_long = df_forecast.melt(
        id_vars=["Tempo"],
        value_vars=opcoes_forecast,
        var_name="Variável",
        value_name="Valor"
    )

    chart_multi = (
        alt.Chart(df_forecast_long)
        .mark_line()
        .encode(
            x=eixo_x(),
            y="Valor:Q",
            color="Variável:N",
            tooltip=["Tempo", "Variável", "Valor"]
        )
        .properties(width=700, height=400)
    )
    st.altair_chart(chart_multi, use_container_width=True)

    # Seção de Download da Previsão
    st.markdown("### 📥 Exporte os dados da previsão")
    st.write("Baixe os dados da previsão horária para consultar offline.")

    # Dados da previsão em CSV
    csv_forecast = df_forecast.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Baixar dados da previsão (CSV)",
        data=csv_forecast,
        file_name="clima_lavras_previsao.csv",
        mime="text/csv"
    )

  # Gráfico da previsão da temperatura (HTML interativo)
    chart_temp.save("grafico_Temperatura.html")
    with open("grafico_Temperatura.html", "rb") as f:
        st.download_button(
            label="📥 Baixar gráfico da previsão da temperatura (HTML interativo)",
            data=f,
            file_name="grafico_Temperatura.html",
            mime="text/html"
    )

    # Gráfico da previsão do clima (HTML interativo)
    chart_multi.save("grafico_previsao_clima.html")
    with open("grafico_previsao_clima.html", "rb") as f:
        st.download_button(
            label="📥 Baixar gráfico da previsão do clima (HTML interativo)",
            data=f,
            file_name="grafico_previsao_clima.html",
            mime="text/html"
    )
        
with tab2:
    if df_historical.empty:
        st.warning("Nenhum dado disponível para o período selecionado.")
    else:
        st.header(f"🌧️ Precipitação - {start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}")

        area_chart = (
            alt.Chart(df_historical)
            .mark_area(color="skyblue", opacity=0.5)
            .encode(
                x=eixo_x(),
                y="Precipitação (mm):Q",
                tooltip=["Tempo", "Precipitação (mm)"]
            )
            .properties(width=700, height=400)
        )
        st.altair_chart(area_chart, use_container_width=True)

        st.header("🌡️ Temperatura Máxima e Mínima por Dia")
        df_temp = df_historical.melt(
            id_vars=["Tempo"],
            value_vars=["Temperatura Máxima diária (°C)", "Temperatura Mínima diária (°C)"],
            var_name="Tipo",
            value_name="Temperatura"
        )

        color_scale = alt.Scale(
            domain=["Temperatura Máxima diária (°C)", "Temperatura Mínima diária (°C)"],
            range=["red", "blue"]
        )

        bar_chart = (
            alt.Chart(df_temp)
            .mark_bar()
            .encode(
                x=eixo_x(),
                y="Temperatura:Q",
                color=alt.Color("Tipo:N", scale=color_scale),
                tooltip=["Tempo", "Tipo", "Temperatura"]
            )
            .properties(width=700, height=400)
        )
        st.altair_chart(bar_chart, use_container_width=True)

        st.header("📊 Temperatura Máxima, Mínima e Precipitação")
        opcoes_historical = st.multiselect(
            "Selecione variáveis para visualizar:",
            ["Temperatura Máxima diária (°C)", "Temperatura Mínima diária (°C)", "Precipitação (mm)"],
            default=["Temperatura Máxima diária (°C)", "Temperatura Mínima diária (°C)", "Precipitação (mm)"]
        )

        df_historical_long = df_historical.melt(
            id_vars=["Tempo"],
            value_vars=opcoes_historical,
            var_name="Variável",
            value_name="Valor"
        )

        chart_hist = (
            alt.Chart(df_historical_long)
            .mark_line()
            .encode(
                x=eixo_x(),
                y="Valor:Q",
                color="Variável:N",
                tooltip=["Tempo", "Variável", "Valor"]
            )
            .properties(width=700, height=400)
        )
        st.altair_chart(chart_hist, use_container_width=True)

        # Seção de Download do Histórico
        st.markdown("### 📥 Exporte seus dados e gráficos")
        st.write("Baixe os dados e gráficos para analisar ou compartilhar.")

        # Dados históricos em CSV
        csv = df_historical.to_csv(index=False).encode("utf-8")
        st.download_button(
                label="📥 Baixar dados históricos (CSV)",
                data=csv,
                file_name=f"clima_lavras_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
                mime="text/csv"
        )

        # Gráfico histórico em HTML interativo (Precipitação)
        area_chart.save("grafico_precipitacao_clima.html")
        with open("grafico_precipitacao_clima.html", "rb") as f:
            st.download_button(
                label="📥 Baixar gráfico histórico (Precipitação) (HTML interativo)",
                data=f,
                file_name="grafico_precipitacao_clima.html",
                mime="text/html"
            )
        # Gráfico histórico em HTML interativo (Temperatura Máxima e Mínima)
        bar_chart.save("grafico_TempMáx_TempMín_clima.html")
        with open("grafico_TempMáx_TempMín_clima.html", "rb") as f:
            st.download_button(
                label="📥 Baixar gráfico histórico (Temperatura Máxima e Mínima) (HTML interativo)",
                data=f,
                file_name="grafico_TempMáx_TempMín_clima.html",
                mime="text/html"
            )
        # Gráfico histórico em HTML interativo (Temperatura Máxima, Mínima e Precipitação)
        chart_hist.save("grafico_clima.html")
        with open("grafico_clima.html", "rb") as f:
            st.download_button(
                label="📥 Baixar gráfico histórico (Temperatura Máxima, Mínima e Precipitação) (HTML interativo)",
                data=f,
                file_name="grafico_clima.html",
                mime="text/html"
            )

# 6. Estatísticas rápidas + Storytelling

st.subheader(f"📊 Estatísticas rápidas - {start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}")
col1, col2, col3 = st.columns(3)
col1.metric("Temp. Máxima Média", f"{df_historical['Temperatura Máxima diária (°C)'].mean():.1f} °C")
col2.metric("Temp. Mínima Média", f"{df_historical['Temperatura Mínima diária (°C)'].mean():.1f} °C")
col3.metric("Precipitação Total", f"{df_historical['Precipitação (mm)'].sum():.1f} mm")

# Storytelling automático baseado nos dados
if not df_historical.empty:
    # Encontrar o dia mais quente
    dia_quente = df_historical.loc[df_historical["Temperatura Máxima diária (°C)"].idxmax()]
    # Encontrar o dia mais frio
    dia_frio = df_historical.loc[df_historical["Temperatura Mínima diária (°C)"].idxmin()]
    # Encontrar o dia mais chuvoso
    dia_chuvoso = df_historical.loc[df_historical["Precipitação (mm)"].idxmax()]

    # Mostrar storytelling automático
    st.markdown("## 📖 O que os dados contam")

    st.write(
        f"🔥 O dia mais quente foi em **{dia_quente['Tempo'].strftime('%d/%m/%Y')} ({dias_semana[dia_quente['Tempo'].weekday()]})**, "
        f"com máxima de **{dia_quente['Temperatura Máxima diária (°C)']} °C**."
    )

    st.write(
        f"❄️ O dia mais frio foi em **{dia_frio['Tempo'].strftime('%d/%m/%Y')} ({dias_semana[dia_frio['Tempo'].weekday()]})**, "
        f"com mínima de **{dia_frio['Temperatura Mínima diária (°C)']} °C**."
    )

    st.write(
        f"🌧️ O dia mais chuvoso foi em **{dia_chuvoso['Tempo'].strftime('%d/%m/%Y')} ({dias_semana[dia_chuvoso['Tempo'].weekday()]})**, "
        f"com precipitação de **{dia_chuvoso['Precipitação (mm)']} mm**."
    )

    # Comparação geral: se choveu muito ou pouco
    chuva_total = df_historical["Precipitação (mm)"].sum()
    if chuva_total > 100:
        st.success("💡 Este período foi marcado por chuvas abundantes, acima de 100 mm no total.")
    else:
        st.info("💡 Este período teve pouca chuva, com menos de 100 mm acumulados.")
