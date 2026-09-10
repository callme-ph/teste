import io
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import control as ct
import sympy as sp
import cmath

from lgr_engine import (
    lgr_completo,
    parse_tf_expression,
    parse_coeffs_str,
    parse_zpk,
    format_complex,
    PRESETS,
)

st.set_page_config(
    page_title="LGR Explorer - Lugar Geométrico das Raízes",
    page_icon="src/renderer/app-icon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .step-header {
        font-weight: 600;
        color: #1E40AF;
    }
    .metric-box {
        background: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 10px 15px;
        border-radius: 4px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

col_title, col_badge = st.columns([3, 1])
with col_title:
    st.markdown('<div class="main-title">Lugar Geométrico das Raízes (LGR)</div>',
                unsafe_allow_html=True)
    
st.sidebar.header("Configuração da Função")

input_mode = st.sidebar.radio(
    "Modo de Entrada da Função de Transferência:",
    [
        "Expressão Algébrica",
        "Coeficientes Polinomiais",
        "Polos, Zeros e Ganho",
        "Exemplos Clássicos",
    ],
    index=0,
)

num_coeffs = None
den_coeffs = None
latex_exp = ""
latex_fac = ""
error_msg = None
preset_desc = ""
ponto = ""

if input_mode == "Expressão Algébrica":
    st.sidebar.markdown(
        "**Digite a função $G(s)$ em função da variável `s`:**")
    expr_default = "(s + 2) / (s * (s + 1) * (s + 4))"
    expr_input = st.sidebar.text_input(
        "Expressão G(s):",
        value=expr_default,
        help="Exemplos: (s + 2) / (s*(s+1)*(s+4)), 10 / (s^3 + 2s^2 + 2s), 1/(s^2+4)",
    )

    ponto_input = st.sidebar.text_input(
        "Avaliar se ponto pertence á LGR",
        value=ponto,
        help="Exemplo: 0.5+1j ou -1.2",
    )

    try:
        num_coeffs, den_coeffs, latex_exp, latex_fac = parse_tf_expression(
            expr_input)
    except Exception as e:
        error_msg = f"Erro na expressão: {e}"

elif input_mode == "Coeficientes Polinomiais":
    st.sidebar.markdown(
        "**Digite os coeficientes em ordem decrescente de potência ($s^n, \dots, s^0$):**")
    num_input = st.sidebar.text_input(
        "Numerador N(s):", value="1, 2", help="Ex: 1, 2 para (s + 2)")
    den_input = st.sidebar.text_input(
        "Denominador D(s):", value="1, 5, 4, 0", help="Ex: 1, 5, 4, 0 para s³ + 5s² + 4s")
    try:
        num_coeffs = parse_coeffs_str(num_input)
        den_coeffs = parse_coeffs_str(den_input)

        s = sp.Symbol('s')
        poly_num = sp.Poly.from_list(num_coeffs, gens=s)
        poly_den = sp.Poly.from_list(den_coeffs, gens=s)
        latex_exp = rf"G(s) = \frac{{{sp.latex(poly_num.as_expr())}}}{{{sp.latex(poly_den.as_expr())}}}"
        latex_fac = rf"G(s) = \frac{{{sp.latex(sp.factor(poly_num.as_expr()))}}}{{{sp.latex(sp.factor(poly_den.as_expr()))}}}"
    except Exception as e:
        error_msg = f"Erro nos coeficientes: {e}"

elif input_mode == "Polos, Zeros e Ganho":
    st.sidebar.markdown(
        "**Forma Fatorada $K \cdot \\frac{\\prod (s - z_i)}{\\prod (s - p_i)}$:**")
    k_val = st.sidebar.number_input("Ganho K:", value=1.0, step=0.5)
    zeros_input = st.sidebar.text_input(
        "Zeros (separados por vírgula):", value="-2", help="Ex: -2 ou -1+2j, -1-2j")
    poles_input = st.sidebar.text_input(
        "Polos (separados por vírgula):", value="0, -1, -4", help="Ex: 0, -1, -4 ou -1+1j, -1-1j")
    try:
        num_coeffs, den_coeffs = parse_zpk(zeros_input, poles_input, k_val)
        s = sp.Symbol('s')
        poly_num = sp.Poly.from_list(num_coeffs, gens=s)
        poly_den = sp.Poly.from_list(den_coeffs, gens=s)
        latex_exp = rf"G(s) = \frac{{{sp.latex(poly_num.as_expr())}}}{{{sp.latex(poly_den.as_expr())}}}"
        latex_fac = rf"G(s) = \frac{{{sp.latex(sp.factor(poly_num.as_expr()))}}}{{{sp.latex(sp.factor(poly_den.as_expr()))}}}"
    except Exception as e:
        error_msg = f"Erro em zeros/polos: {e}"

elif input_mode == "Exemplos Clássicos":
    preset_choice = st.sidebar.selectbox(
        "Selecione um caso de estudo clássico:", list(PRESETS.keys()))
    chosen = PRESETS[preset_choice]
    preset_desc = chosen["desc"]
    st.sidebar.info(f"**Descrição do caso:**\n{preset_desc}")
    num_coeffs = chosen["num"]
    den_coeffs = chosen["den"]
    try:
        s = sp.Symbol('s')
        poly_num = sp.Poly.from_list(num_coeffs, gens=s)
        poly_den = sp.Poly.from_list(den_coeffs, gens=s)
        latex_exp = rf"G(s) = \frac{{{sp.latex(poly_num.as_expr())}}}{{{sp.latex(poly_den.as_expr())}}}"
        latex_fac = rf"G(s) = \frac{{{sp.latex(sp.factor(poly_num.as_expr()))}}}{{{sp.latex(sp.factor(poly_den.as_expr()))}}}"
    except Exception as e:
        error_msg = f"Erro no preset: {e}"

st.sidebar.markdown("---")
custom_title = st.sidebar.text_input(
    "Título do Gráfico:", value="Lugar Geométrico das Raízes")

if error_msg:
    st.error(f"Erro: {error_msg}")
else:
    with st.container():
        st.markdown("#### Função de Transferência em Malha Aberta:")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Forma Polinomial Expandida:**")
            st.latex(latex_exp)
        with c2:
            st.markdown("**Forma Fatorada (Polos e Zeros):**")
            st.latex(latex_fac)

    st.markdown("---")

    try:
        fig, ax, detalhes = lgr_completo(
            num_coeffs, den_coeffs, titulo=custom_title, show_plot=False)

        tab_grafico, tab_passos = st.tabs(
            ["Gráfico do LGR (7 Passos)", "Memorial de Cálculo Passo a Passo"])

        with tab_grafico:
            st.pyplot(fig, use_container_width=True)

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
            st.download_button(
                label="Baixar Gráfico em Alta Resolução (PNG 300 DPI)",
                data=buf.getvalue(),
                file_name="lugar_geometrico_das_raizes.png",
                mime="image/png",
            )

        with tab_passos:
            st.markdown("### Passos")

            # Passo 1, 2 e 3
            with st.expander("**Passo 1, 2 e 3: Ramos, Polos, Zeros e Simetria**", expanded=True):
                c_p1, c_p2, c_p3 = st.columns(3)
                with c_p1:
                    st.markdown(
                        f"**Número de Polos ($P$):** `{detalhes['P']}`")
                    polos_fmt = [format_complex(p) for p in detalhes['polos']]
                    st.write(f"Polos em: {', '.join(polos_fmt)}")
                with c_p2:
                    st.markdown(
                        f"**Número de Zeros ($Z$):** `{detalhes['Z']}`")
                    if detalhes['Z'] > 0:
                        zeros_fmt = [format_complex(z, 4)
                                     for z in detalhes['zeros']]
                        st.write(f"Zeros em: {', '.join(zeros_fmt)}")
                    else:
                        st.write(
                            "Nenhum zero finito nesta função de transferência.")
                with c_p3:
                    st.markdown(
                        f"**Total de Ramos ($n = \max(P, Z)$):** `{detalhes['ramos']}`")
                    st.write(
                        f"• Ramos partem dos **{detalhes['P']} polos** quando $K \\to 0$.")
                    st.write(
                        f"• Ramos terminam nos **{detalhes['Z']} zeros** (e {max(0, detalhes['P'] - detalhes['Z'])} em $\\infty$) quando $K \\to \\infty$.")

                st.markdown(
                    "**Simetria:** O LGR é perfeitamente simétrico em relação ao Eixo Real ($\sigma$), pois polos e zeros complexos sempre ocorrem em pares conjugados.")

            # Passo 4
            with st.expander("**Passo 4: Assíntotas e Centroide**", expanded=True):
                P, Z = detalhes['P'], detalhes['Z']
                if P > Z:
                    st.markdown(
                        f"Como $P > Z$, existem **{P - Z} ramo(s)** que terminam no infinito ao longo de assíntotas.")
                    st.markdown(r"**Centroide das Assíntotas ($\sigma_a$):**")
                    st.latex(
                        rf"\sigma_a = \frac{{\sum \text{{Polos}} - \sum \text{{Zeros}}}}{{P - Z}} = \frac{{{np.sum(np.real(detalhes['polos'])):.4f} - ({np.sum(np.real(detalhes['zeros'])):.4f})}}{{{P - Z}}} = {detalhes['centroide']:.4f}")

                    st.markdown(
                        r"**Ângulos das Assíntotas ($\theta_k$):** $\theta_k = \frac{(2k + 1) \cdot 180^\circ}{P - Z}$")
                    ang_text = ", ".join(
                        [f"k={a['k']}: **{a['graus']:.4f}°**" for a in detalhes['angulos_assintotas']])
                    st.write(f"Ângulos calculados: {ang_text}")
                else:
                    st.info(
                        "Como $P \le Z$, todos os ramos terminam nos zeros finitos. Não há assíntotas para o infinito.")

            # Passo 5
            with st.expander("**Passo 5: Pontos de Partida e Retorno (Break-in / Breakaway)**", expanded=True):
                st.markdown(
                    r"Obtidos a partir da derivada do ganho: $\frac{dK}{ds} = 0 \iff N'(s)D(s) - N(s)D'(s) = 0$.")
                if detalhes['break_points']:
                    for bp in detalhes['break_points']:
                        st.success(
                            f"**Ponto no eixo real:** $s = {bp['s']:.4f}$ com ganho correspondente **$K = {bp['K']:.4f}$**")
                else:
                    st.write(
                        "Nenhum ponto de break-in ou breakaway válido com $K > 0$ no eixo real.")

            # Passo 6
            with st.expander("**Passo 6: Cruzamento do Eixo Imaginário ($j\omega$)**", expanded=True):
                st.markdown(
                    r"Determina o limite de estabilidade do sistema em malha fechada (frequência de oscilação crítica $\omega_{cruz}$ e ganho crítico $K_{crit}$).")
                if detalhes['jw_cruzamentos']:
                    seen_jw = set()
                    for jw in detalhes['jw_cruzamentos']:
                        key = (round(abs(jw['w']), 2), round(jw['K'], 2))
                        if key in seen_jw:
                            continue
                        seen_jw.add(key)
                        st.warning(
                            f"**Cruzamento detectado em:** $s = \pm j{abs(jw['w']):.4f}$ para o Ganho Crítico **$K = {jw['K']:.4f}$**")
                else:
                    st.write(
                        "Nenhum cruzamento com o eixo imaginário encontrado na faixa de ganho analisada.")

            # Passo 7
            with st.expander("**Passo 7: Ângulos de Partida ($\theta_d$) e Chegada ($\theta_a$)**", expanded=True):
                tem_partida = bool(detalhes.get('angulos_partida'))
                tem_chegada = bool(detalhes.get('angulos_chegada'))

                if tem_partida or tem_chegada:
                    if tem_partida:
                        st.markdown(
                            r"**Ângulo de Partida em Polos Complexos ($\theta_d$):**")
                        st.caption(
                            r"Condição angular: $\theta_d = 180^\circ + \sum \angle(p - z_i) - \sum \angle(p - p_j)$")
                        for ap in detalhes['angulos_partida']:
                            p_str = format_complex(ap['polo'], 4)
                            st.info(
                                f"Polo $p = {p_str}$: **$\\theta_d = {ap['angulo']:.4f}^\\circ$**")
                    if tem_chegada:
                        st.markdown(
                            r"**Ângulo de Chegada em Zeros Complexos ($\theta_a$):**")
                        st.caption(
                            r"Condição angular: $\theta_a = 180^\circ + \sum \angle(z - p_i) - \sum \angle(z - z_j)$")
                        for ac in detalhes['angulos_chegada']:
                            z_str = format_complex(ac['zero'])
                            st.success(
                                f"Zero $z = {z_str}$: **$\\theta_a = {ac['angulo']:.4f}^\\circ$**")
                else:
                    st.write(
                        "A função de transferência não possui polos ou zeros complexos conjugados (todas as singularidades são reais).")

        if 'ponto_input' in locals() and ponto_input.strip() != "":
            st.markdown("---")
            st.markdown("### Avaliação de Ponto Específico no LGR")
        
            try:
                # Tratamento da entrada do usuário (aceita "0.5+1j", "-1.2", "-1+2j", etc.)
                s0_str = ponto_input.replace(" ", "").replace("i", "j")
                s0 = complex(s0_str)
        
                polos = detalhes['polos']
                zeros = detalhes['zeros']
        
                # Verificar se s0 coincide exatamente com algum polo ou zero
                e_polo = any(np.isclose(s0, p, atol=1e-5) for p in polos)
                e_zero = any(np.isclose(s0, z, atol=1e-5) for z in zeros)
        
                if e_polo:
                    st.info(
                        f"O ponto $s = {format_complex(s0)}$ é um **polo** do sistema em malha aberta (pertence ao LGR com $K = 0$).")
                elif e_zero:
                    st.info(
                        f"O ponto $s = {format_complex(s0)}$ é um **zero** do sistema em malha aberta (pertence ao LGR quando $K \\to \\infty$).")
                else:
                    # 1. CONDIÇÃO DE ÂNGULO
                    # Modulo dos vetores (s0 - zi) e (s0 - pj)
                    ang_zeros_rad = sum(cmath.phase(s0 - z) for z in zeros)
                    ang_polos_rad = sum(cmath.phase(s0 - p) for p in polos)
        
                    # Ângulo total em graus G(s0)
                    ang_total_rad = ang_zeros_rad - ang_polos_rad
                    ang_total_deg = np.degrees(ang_total_rad)
        
                    # Normalização do ângulo para a faixa [-180°, 180°]
                    ang_norm = (ang_total_deg + 180) % 360 - 180
        
                    # Tolerância para considerar 180° (ex: erro < 1.0°)
                    tolerancia_ang = 5.0
                    erro_angulo = abs(abs(ang_norm) - 180)
        
                    pertence_lgr = erro_angulo <= tolerancia_ang and erro_angulo >= tolerancia_ang * -1
        
                    # 2. CONDIÇÃO DE MÓDULO
                    # G_módulo = |prod(s0 - zi) / prod(s0 - pj)|
                    mod_zeros = np.prod([abs(s0 - z)
                                        for z in zeros]) if len(zeros) > 0 else 1.0
                    mod_polos = np.prod([abs(s0 - p) for p in polos])
        
                    if mod_zeros != 0:
                        K_calculado = mod_polos / mod_zeros
                    else:
                        K_calculado = np.inf
        
                    # APRESENTAÇÃO DOS RESULTADOS NO STREAMLIT
                    col_res1, col_res2 = st.columns(2)
        
                    with col_res1:
                        st.markdown("**1. Condição de Ângulo:**")
                        st.latex(
                            r"\angle G(s_0) = \sum \angle(s_0 - z_i) - \sum \angle(s_0 - p_j)")
                        st.write(f"• Ângulo calculado em $s_0$: **{ang_norm:.4f}°**")
        
                        if pertence_lgr:
                            st.success(
                                f"✅ **Pertence ao LGR!**\n\nO ângulo é aproximadamente $\\pm 180^\\circ$ (Erro: {erro_angulo:.4f}°).")
                        else:
                            st.error(
                                f"❌ **NÃO pertence ao LGR.**\n\nO ângulo difere de $\\pm 180^\\circ$ em {erro_angulo:.4f}°.")
        
                    with col_res2:
                        st.markdown("**2. Condição de Módulo:**")
                        st.latex(
                            r"K = \frac{\prod |s_0 - p_j|}{\prod |s_0 - z_i|} = \frac{1}{|G(s_0)|}")
                        if pertence_lgr:
                            st.metric(label="Ganho K correspondente:",
                                      value=f"{K_calculado:.4f}")
                            st.caption(
                                "Este é o valor do ganho necessário para posicionar um polo de malha fechada exatamente sobre este ponto.")
                        else:
                            st.write(
                                f"• Módulo $|G(s_0)|^{-1}$ para este ponto: **{K_calculado:.4f}**")
                            st.caption(
                                "Como a condição de ângulo não foi satisfeita, este ganho não produzirá raízes exatamente neste ponto.")
        
            except ValueError:
                st.warning(
                    "Formato de número complexo inválido. Digite no formato ex: `0.5+1j`, `-2`, `-1-2j`.")
            except Exception as e:
                st.error(f"Erro ao avaliar ponto: {e}")

    except Exception as e:
        st.error(f"Erro no cálculo do Lugar Geométrico das Raízes: {e}")
