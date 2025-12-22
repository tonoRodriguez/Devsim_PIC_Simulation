# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 11:44:13 2025

@author: anenr
"""
#Importante no olvidar que la malla este en micras!!!

# ============================================================
# 0. IMPORTS Y CONSTANTES FÍSICAS GLOBALES
# ============================================================

# Importar DEVSIM y utilidades de modelos
# Definir constantes físicas: q, k, eps0
# Definir constantes del material: eps_si, eps_ox
# Definir parámetros globales de simulación (T, etc.)

from devsim import *
from devsim.python_packages.model_create import CreateNodeModel, CreateSolution

q = 1.6e-19  # coul
k = 1.3806503e-23  # J/K
#eps_0 = 8.85e-14  # F/cm^2 -> Pasar a micrometro2!!!!
eps_0 = 8.85e-6  # F/µm²

eps_si = 11.1
eps_ox = 3.9

T      = 300 # K



# ============================================================
# 1. CREACIÓN DEL DISPOSITIVO Y CARGA DE LA MALLA
# ============================================================

# Definir nombre del dispositivo
# create_gmsh_mesh(...)
# add_gmsh_region(...)  -> Si
# add_gmsh_region(...)  -> SiO2
# add_gmsh_contact(...) -> contacto inferior
# add_gmsh_contact(...) -> contacto superior
# finalize_mesh(...)
# create_device(...)

device = "SOI_Waveguide"
region = "BOX"
core = "Core"

# --- Importar malla ---
create_gmsh_mesh(mesh=device, file="SiliconWaveguide.msh")

# --- Regiones ---
add_gmsh_region(mesh=device, gmsh_name="SiO2",    region=region, material="SiO2")
add_gmsh_region(mesh=device, gmsh_name="Si",      region=core, material="Silicon")


add_gmsh_contact(mesh=device, gmsh_name="bot_contact", region=region,  material="metal", name="bot")
add_gmsh_contact(mesh=device, gmsh_name="top_contact", region=region,  material="metal", name="top")

# --- Finalizar ---
finalize_mesh(mesh=device)
create_device(mesh=device, device=device)


# ============================================================
# 2. DEFINICIÓN DE PARÁMETROS DE MATERIAL (CONSTANTES)
# ============================================================

# ---- 2.1 Parámetros del Silicio (Si)
# set_parameter: Permittivity
# set_parameter: ElectronCharge
# set_parameter: n_i
# set_parameter: T, kT, Vt
# set_parameter: movilidades (mu_n, mu_p)
# set_parameter: parámetros SRH (taun, taup, n1, p1)

# TODO: make this temperature dependent
#n_i = 1.0e10  # #/cm^3
n_i = n_i = 0.01  # #/µm^3

# constant in our approximation
mu_n = 400 #reviar poco dopados 1350
mu_p = 200 #serian 480


set_parameter(
    device=device, region=core, name="Permittivity", value=eps_si * eps_0
)
set_parameter(device=device, region=core, name="ElectronCharge", value=q)
set_parameter(device=device, region=core, name="n_i", value=n_i)
set_parameter(device=device, region=core, name="T", value=T)
set_parameter(device=device, region=core, name="kT", value=k * T)
set_parameter(device=device, region=core, name="V_t", value=k * T / q)
set_parameter(device=device, region=core, name="mu_n", value=mu_n)
set_parameter(device=device, region=core, name="mu_p", value=mu_p)
# default SRH parameters
set_parameter(device=device, region=core, name="n1", value=n_i)
set_parameter(device=device, region=core, name="p1", value=n_i)
set_parameter(device=device, region=core, name="taun", value=1e-5) #Estos valores estan mal
set_parameter(device=device, region=core, name="taup", value=1e-5) #Estos valores estan mal

#Ni node 
CreateNodeModel(
    device,
    core,
    "n_i_node",
    "n_i"
)


# ---- 2.2 Parámetros del Óxido (SiO2)
# set_parameter: Permittivity
# (NO movilidades, NO n_i, NO SRH)


set_parameter(
    device=device, region=region, name="Permittivity", value=eps_0 * eps_ox
)
set_parameter(device=device, region=region, name="ElectronCharge", value=q)

# ============================================================
# 3. DEFINICIÓN DE SOLUCIONES (VARIABLES DESCONOCIDAS)
# ============================================================

# ---- 3.1 En Silicio
# No es claro si tengo que usar node_solution o CreateSolution = crea variable + inicialización segura 
#node_solution = nivel bajo (espera que sepas lo que haces)
# CreateSolution: Electrons (n)
# CreateSolution: Holes (p) 

CreateSolution(device = device, region = core, name= "Potential")
CreateSolution(device = device, region = core, name= "Electrons")
CreateSolution(device = device, region = core, name= "Holes")


# Inicialización física de portadores (MUY IMPORTANTE)
set_node_values(
    device=device,
    region=core,
    name="Electrons",
    init_from="n_i_node"
)

set_node_values(
    device=device,
    region=core,
    name="Holes",
    init_from="n_i_node"
)

# ---- 3.2 En Óxido
# CreateSolution: Potential
# (NO Electrons, NO Holes)

node_solution(device = device, region = region, name= "Potential")


# ============================================================
# 4. DEFINICIÓN DE DOPAJE Y CARGAS FIJAS
# ============================================================

# ---- 4.1 Silicio intrínseco
# NO hay dopaje
# Donors = 0
# Acceptors = 0
# NetDoping = 0
# La carga en Si vendrá SOLO de n y p (variables solución)

# ---- 4.2 Carga fija por TID en SiO2
# Pares e–h generados por radiación → huecos atrapados
# set_parameter: OxideTrapDensity = 3.5e6   # cm^-3
# CreateNodeModel: FixedCharge = +q * OxideTrapDensity



# set_parameter(
#     device=device,
#     region=region,
#     name="OxideTrapDensity",
#     value=3.5e6  # cm^-3
# )

# CreateNodeModel(
#     device,
#     region,
#     "FixedCharge",
#     "ElectronCharge * OxideTrapDensity"
# )
# ============================================================
# 5. MODELOS DE PORTADORES EN SILICIO
# ============================================================

# ---- 5.1 Concentraciones de equilibrio
# CreateNodeModel: IntrinsicElectrons (Boltzmann)
# CreateNodeModel: IntrinsicHoles (Boltzmann)
# NO se definen como NodeModel
# NO se usa Boltzmann en DD

G_value = 1.782e7  # cm^-3 s^-1

set_parameter(
    device=device,
    region=core,
    name="G_RAD",
    value=G_value   # cm^-3 s^-1
)



# ---- 5.2 Carga total para Poisson
# CreateNodeModel: Charge =
#   -q * (p - n + NetDoping)


CreateNodeModel(
    device,
    "Core",
    "Charge",
    "ElectronCharge * (Holes - Electrons)"
)


# ============================================================
# 6. MODELOS DE GENERACIÓN–RECOMBINACIÓN
# ============================================================

# ---- 6.1 Recombination SRH
# CreateNodeModel: R_SRH (función de n, p, taun, taup)
USRH = "(Electrons*Holes - n_i^2)/" \
       "(taup*(Electrons + n1) + taun*(Holes + p1))"

dUSRHdn="simplify(diff(%s , Electrons))" % USRH
dUSRHdp="simplify(diff(%s , Holes))" % USRH

# Modelo SRH
node_model(
    device=device,
    region="Core",
    name="USRH",
    equation=USRH
)

# Derivadas para Newton
node_model(
    device=device,
    region="Core",
    name="USRH:Electrons",
    equation=dUSRHdn
)

node_model(
    device=device,
    region="Core",
    name="USRH:Holes",
    equation=dUSRHdp
)
# ---- 6.2 Generación por radiación (TID) en Si
# CreateNodeModel: G_rad
# (constante o dependiente de dosis/tiempo)

CreateNodeModel(device, core,  "G_rad", "G_RAD")



# ---- 6.3 Generación total
# CreateNodeModel: G_total = G_rad - R_SRH

CreateNodeModel(device, core, "G_total", "G_rad - USRH")

# ============================================================
# 7. MODELOS DE CAMPO ELÉCTRICO Y FLUJOS
# ============================================================

# ---- 7.1 Campo eléctrico
# CreateEdgeModel: ElectricField

#SiO2
edge_from_node_model(device=device, region=region, node_model="Potential")

edge_model(
    device=device,
    region=region,
    name="ElectricField",
    equation="(Potential@n0 - Potential@n1)*EdgeInverseLength",
)

edge_model(
    device=device,
    region=region,
    name="ElectricField:Potential@n0",
    equation="EdgeInverseLength",
)

edge_model(
    device=device,
    region=region,
    name="ElectricField:Potential@n1",
    equation="-EdgeInverseLength",
)

###
### Model the D Field
###
edge_model(
    device=device, region=region, name="DField", equation="Permittivity*ElectricField"
)

edge_model(
    device=device,
    region=region,
    name="DField:Potential@n0",
    equation="diff(Permittivity*ElectricField, Potential@n0)",
)

edge_model(
    device=device,
    region=region,
    name="DField:Potential@n1",
    equation="-DField:Potential@n0",
)
#Si
edge_from_node_model(device=device, region=core, node_model="Potential")

edge_model(
    device=device,
    region=core,
    name="ElectricField",
    equation="(Potential@n0 - Potential@n1)*EdgeInverseLength",
)

edge_model(
    device=device,
    region=core,
    name="ElectricField:Potential@n0",
    equation="EdgeInverseLength",
)

edge_model(
    device=device,
    region=core,
    name="ElectricField:Potential@n1",
    equation="-EdgeInverseLength",
)

###
### Model the D Field
###
edge_model(
    device=device, region=core, name="DField", equation="Permittivity*ElectricField"
)

edge_model(
    device=device,
    region=core,
    name="DField:Potential@n0",
    equation="diff(Permittivity*ElectricField, Potential@n0)",
)

edge_model(
    device=device,
    region=core,
    name="DField:Potential@n1",
    equation="-DField:Potential@n0",
)

# ---- 7.2 Flujo de Poisson
# CreateEdgeModel: PotentialEdgeFlux
# Ocupo equation aca porque estaba en el ejemplo



# ---- 7.3 Corrientes de electrones y huecos
# CreateEdgeModel: ElectronCurrent (drift + diffusion)
# CreateEdgeModel: HoleCurrent (drift + diffusion)

# ---- 7.3.1 Modelos auxiliares (Einstein)

CreateNodeModel(
    device,
    core,
    "Dn",
    "mu_n * V_t"
)

CreateNodeModel(
    device,
    core,
    "Dp",
    "mu_p * V_t"
)

# ---- 7.3.2 Gradientes de portadores en aristas

edge_from_node_model(device=device, region=core, node_model="Electrons")
edge_from_node_model(device=device, region=core, node_model="Holes")

# ---- 7.3.3 Corriente de ELECTRONES

edge_model(
    device=device,
    region=core,
    name="ElectronCurrent",
    equation=
        "ElectronCharge * ("
        "mu_n * Electrons@n0 * ElectricField"
        " + Dn * (Electrons@n0 - Electrons@n1) * EdgeInverseLength"
        ")"
)

# Derivadas (Newton)
edge_model(
    device=device,
    region=core,
    name="ElectronCurrent:Electrons@n0",
    equation=
        "ElectronCharge * ("
        "mu_n * ElectricField"
        " + Dn * EdgeInverseLength"
        ")"
)

edge_model(
    device=device,
    region=core,
    name="ElectronCurrent:Electrons@n1",
    equation=
        "-ElectronCharge * Dn * EdgeInverseLength"
)

# ---- 7.3.4 Corriente de HUECOS

edge_model(
    device=device,
    region=core,
    name="HoleCurrent",
    equation=
        "ElectronCharge * ("
        "mu_p * Holes@n0 * ElectricField"
        " - Dp * (Holes@n0 - Holes@n1) * EdgeInverseLength"
        ")"
)

#Drivadas (Newton)

edge_model(
    device=device,
    region=core,
    name="HoleCurrent:Holes@n0",
    equation=
        "ElectronCharge * ("
        "mu_p * ElectricField"
        " - Dp * EdgeInverseLength"
        ")"
)

edge_model(
    device=device,
    region=core,
    name="HoleCurrent:Holes@n1",
    equation=
        "ElectronCharge * Dp * EdgeInverseLength"
)


# ============================================================
# 8. ECUACIONES FÍSICAS
# ============================================================

# ---- 8.1 Ecuación de Poisson
# equation: variable = Potential
# node_model = Charge (Si) / FixedCharge (SiO2)
# edge_model = PotentialEdgeFlux


#SiO2
equation(
    device=device,
    region=region,
    name="PotentialEquation",
    variable_name="Potential",
    node_model="FixedCharge",
    edge_model="DField",
)


#Si
#antes sin node_model

equation(
    device=device,
    region=core,
    name="PotentialEquation",
    variable_name="Potential",
    node_model="Charge",
    edge_model="DField",
)


# ---- 8.2 Continuidad de electrones (Si)
# equation: variable = Electrons
# edge_model = ElectronCurrent
# time_node_model = G_total

equation(
    device=device,
    region=core,
    name="ElectronContinuity",
    variable_name="Electrons",
    edge_model="ElectronCurrent",
    time_node_model="G_total",
    variable_update="positive"
    #min_value=1.0
)

# ---- 8.3 Continuidad de huecos (Si)
# equation: variable = Holes
# edge_model = HoleCurrent
# time_node_model = G_total

equation(
    device=device,
    region=core,
    name="HoleContinuity",
    variable_name="Holes",
    edge_model="HoleCurrent",
    time_node_model="G_total",
    variable_update="positive"
    #min_value=1.0
)


# ============================================================
# 9. CONDICIONES DE CONTORNO
# ============================================================

# ---- 9.1 Contactos eléctricos
# set_contact_bias: contacto inferior (0 V)
# set_contact_bias: contacto superior (0 V)


###
### Contact models and equations
###
for c in ("top", "bot"):
    contact_node_model(
        device=device, contact=c, name="%s_bc" % c, equation="Potential - %s_bias" % c
    )

    contact_node_model(
        device=device, contact=c, name="%s_bc:Potential" % c, equation="1"
    )

    contact_equation(
        device=device,
        contact=c,
        name="PotentialEquation",
        node_model="%s_bc" % c,
        edge_charge_model="DField",
    )
    
    
###
### Set the contact
###
set_parameter(device=device, name="top_bias", value=0.0)
set_parameter(device=device, name="bot_bias", value=0.0)

# ---- 9.2 Condiciones de portadores en contactos en Si
# electron/hole surface recombination
# ohmic contacts (n = n0, p = p0)

# ---- 9.2.1 Valores de equilibrio en Silicio intrínseco

# CreateNodeModel(
#     device,
#     core,
#     "n0",
#     "n_i"
# )

# CreateNodeModel(
#     device,
#     core,
#     "p0",
#     "n_i"
# )

# # ---- 9.2.2 Modelos de contacto para electrones

# for c in ("top", "bot"):
#     contact_node_model(
#         device=device,
#         contact=c,
#         name="Electron_bc_%s" % c,
#         equation="Electrons - n0"
#     )

#     contact_node_model(
#         device=device,
#         contact=c,
#         name="Electron_bc_%s:Electrons" % c,
#         equation="1"
#     )

#     contact_equation(
#         device=device,
#         contact=c,
#         name="ElectronContinuity",
#         node_model="Electron_bc_%s" % c,
#         edge_current_model="ElectronCurrent"
#     )
    
# # ---- 9.2.2 Modelos de contacto para huecos

# for c in ("top", "bot"):
#     contact_node_model(
#         device=device,
#         contact=c,
#         name="Hole_bc_%s" % c,
#         equation="Holes - p0"
#     )

#     contact_node_model(
#         device=device,
#         contact=c,
#         name="Hole_bc_%s:Holes" % c,
#         equation="1"
#     )

#     contact_equation(
#         device=device,
#         contact=c,
#         name="HoleContinuity",
#         node_model="Hole_bc_%s" % c,
#         edge_current_model="HoleCurrent"
#     )


# ============================================================
# 10. INICIALIZACIÓN DE LA SOLUCIÓN
# ============================================================

# ---- 10.1 Inicialización electrostática
# solve(type="dc") solo Poisson

# solve -type dc -absolute_error 1.0 -relative_error 1e-10 -maximum_iterations 100 -solver_type iterative

set_parameter(
    device=device,
    region=core,
    name="G_RAD",
    value=0.0
)

solve(
    type="dc",
    absolute_error=1.0,
    relative_error=1e-10,
    maximum_iterations=30,
    solver_type="direct",
)



# ---- 10.2 Inicialización de portadores
# solve(type="dc") Poisson + DD sin generación


solve(
    type="dc",
    absolute_error=1e-12,
    relative_error=1e-10,
    maximum_iterations=50,
    solver_type="direct",
)


# ============================================================
# 11. SIMULACIÓN TID
# ============================================================

# ---- 11.1 Activar G_rad

set_parameter(
    device=device,
    region=core,
    name="G_RAD",
    value=1.782e7  # cm^-3 s^-1
)

# ---- 11.2 Simulación DC (estado estacionario)

solve(
    type="dc",
    absolute_error=1e-14,
    relative_error=1e-12,
    maximum_iterations=80,
    solver_type="direct",
)

# o
# ---- 11.3 Simulación Transiente (dosis vs tiempo)

"""
#Definir tiempo

t_end = 1.0      # segundos
dt    = 1e-3


solve(
    type="transient",
    tdelta=dt,
    tstop=t_end,
    absolute_error=1e-14,
    relative_error=1e-12,
    maximum_iterations=30,
)

"""


# ============================================================
# 12. POST-PROCESADO Y DEBUG
# ============================================================

# print_node_values(...)
# plot de potencial, campo eléctrico
# perfil de carga atrapada
# densidad de portadores


write_devices(file="SOI_WG", type="vtk")

# ============================================================
# 13. BARRIDOS PARAMÉTRICOS (OPCIONAL)
# ============================================================

# loop sobre:
# - dosis
# - densidad de trampas
# - bias
# guardar resultados



# ============================================================
# FIN DEL SCRIPT
# ============================================================
