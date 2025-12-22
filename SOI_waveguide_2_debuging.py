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
from devsim.python_packages.model_create import CreateNodeModel, CreateSolution, CreateNodeModelDerivative

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


#reset_devsim()

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


# ---- 3.2 En Óxido
# CreateSolution: Potential
# (NO Electrons, NO Holes)

CreateSolution(device = device, region = region, name= "Potential")


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

set_parameter(
    device=device,
    region=region,
    name="OxideTrapDensity",
    value=3.5e16  # mm^-3
)

CreateNodeModel(
    device,
    region,
    "FixedCharge",
    "ElectronCharge * OxideTrapDensity"
)

# ============================================================
# 5. MODELOS DE PORTADORES EN SILICIO
# ============================================================

# ---- 5.1 Concentraciones de equilibrio
# CreateNodeModel: IntrinsicElectrons (Boltzmann)
# CreateNodeModel: IntrinsicHoles (Boltzmann)
# NO se definen como NodeModel
# NO se usa Boltzmann en DD

#Si

elec_i = "n_i*exp(Potential/V_t)"
hole_i = "n_i^2/IntrinsicElectrons"
charge_i = "kahan3(IntrinsicHoles, -IntrinsicElectrons, 0)"
pcharge_i = "-ElectronCharge * IntrinsicCharge"


# require NetDoping
for i in (
    ("IntrinsicElectrons", elec_i),
    ("IntrinsicHoles", hole_i),
    ("IntrinsicCharge", charge_i),
    ("PotentialIntrinsicCharge", pcharge_i),
):
    n = i[0]
    e = i[1]
    CreateNodeModel(device, core, n, e)
    CreateNodeModelDerivative(device, core, n, e, "Potential")

# # require NetDoping
# for i in (
#     ("IntrinsicElectrons", elec_i),
#     ("IntrinsicHoles", hole_i),
#     ("IntrinsicCharge", charge_i),
#     ("PotentialIntrinsicCharge", pcharge_i),
# ):
#     n = i[0]
#     e = i[1]
#     CreateNodeModel(device, region, n, e)
#     CreateNodeModelDerivative(device, region, n, e, "Potential")
    
# ### TODO: Edge Average Model
# for i in (
#     ("ElectricField", "(Potential@n0-Potential@n1)*EdgeInverseLength"),
#     ("PotentialEdgeFlux", "Permittivity * ElectricField"),
# ):
#     n = i[0]
#     e = i[1]
#     CreateEdgeModel(device, region, n, e)
#     CreateEdgeModelDerivatives(device, region, n, e, "Potential")

# ---- 5.2 Carga total para Poisson
# CreateNodeModel: Charge =
#   -q * (p - n + NetDoping)





# ============================================================
# 6. MODELOS DE GENERACIÓN–RECOMBINACIÓN
# ============================================================

# ---- 6.1 Recombination SRH
# CreateNodeModel: R_SRH (función de n, p, taun, taup)

# Modelo SRH


# Derivadas para Newton


# ---- 6.2 Generación por radiación (TID) en Si
# CreateNodeModel: G_rad
# (constante o dependiente de dosis/tiempo)


# ---- 6.3 Generación total
# CreateNodeModel: G_total = G_rad - R_SRH


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

# ---- 7.3.2 Gradientes de portadores en aristas

#edge_from_node_model(device=device, region=core, node_model="Electrons")
#edge_from_node_model(device=device, region=core, node_model="Holes")

# ---- 7.3.3 Corriente de ELECTRONES


# ---- 7.3.4 Corriente de HUECOS


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
    edge_model="DField"
)


#Si
#antes sin node_model

equation(
    device=device,
    region=core,
    name="PotentialEquation",
    variable_name="Potential",
    node_model="PotentialIntrinsicCharge",
    edge_model="DField",
    variable_update="log_damp"
)



# ---- 8.2 Continuidad de electrones (Si)
# equation: variable = Electrons
# edge_model = ElectronCurrent
# time_node_model = G_total



# ---- 8.3 Continuidad de huecos (Si)
# equation: variable = Holes
# edge_model = HoleCurrent
# time_node_model = G_total




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
set_parameter(device=device, name="top_bias", value=5.0)
set_parameter(device=device, name="bot_bias", value=2.0)

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

# set_parameter(
#     device=device,
#     region=core,
#     name="G_RAD",
#     value=0.0
# )

# solve(
#     type="dc",
#     absolute_error=1.0,
#     relative_error=1e-10,
#     maximum_iterations=30,
#     solver_type="direct",
# )



# # ---- 10.2 Inicialización de portadores
# # solve(type="dc") Poisson + DD sin generación





# # ============================================================
# # 11. SIMULACIÓN TID
# # ============================================================

# # ---- 11.1 Activar G_rad



# # ---- 11.2 Simulación DC (estado estacionario)



# # o
# # ---- 11.3 Simulación Transiente (dosis vs tiempo)

# """
# #Definir tiempo

# t_end = 1.0      # segundos
# dt    = 1e-3


# solve(
#     type="transient",
#     tdelta=dt,
#     tstop=t_end,
#     absolute_error=1e-14,
#     relative_error=1e-12,
#     maximum_iterations=30,
# )

# """


# # ============================================================
# # 12. POST-PROCESADO Y DEBUG
# # ============================================================

# # print_node_values(...)
# # plot de potencial, campo eléctrico
# # perfil de carga atrapada
# # densidad de portadores

# #get_node_model_values(device=device, region=region, name="Potential"
# #rho = get_node_model_values(device=device, region=region, name="FixedCharge")

# write_devices(file="SOI_WG", type="vtk")

# # ============================================================
# # 13. BARRIDOS PARAMÉTRICOS (OPCIONAL)
# # ============================================================

# # loop sobre:
# # - dosis
# # - densidad de trampas
# # - bias
# # guardar resultados

get_edge_model_list()

# # ============================================================
# # FIN DEL SCRIPT
# ============================================================
