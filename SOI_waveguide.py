# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 09:45:22 2025

@author: anenr
"""

from devsim import *
from devsim.python_packages.model_create import CreateNodeModel, CreateSolution


q = 1.6e-19  # coul
k = 1.3806503e-23  # J/K
eps_0 = 8.85e-14  # F/cm^2
# T      = 300 # K

# TODO: make this temperature dependent
n_i = 1.0e10  # #/cm^3
# constant in our approximation
mu_n = 400
mu_p = 200

def SetSiliconParameters(device, region, T):
    """
    Sets physical parameters assuming constants
    """
    #### TODO: make T a free parameter and T dependent parameters as models
    set_parameter(
        device=device, region=region, name="Permittivity", value=eps_si * eps_0
    )
    set_parameter(device=device, region=region, name="ElectronCharge", value=q)
    set_parameter(device=device, region=region, name="n_i", value=n_i)
    set_parameter(device=device, region=region, name="T", value=T)
    set_parameter(device=device, region=region, name="kT", value=k * T)
    set_parameter(device=device, region=region, name="V_t", value=k * T / q)
    set_parameter(device=device, region=region, name="mu_n", value=mu_n)
    set_parameter(device=device, region=region, name="mu_p", value=mu_p)
    # default SRH parameters
    set_parameter(device=device, region=region, name="n1", value=n_i)
    set_parameter(device=device, region=region, name="p1", value=n_i)
    set_parameter(device=device, region=region, name="taun", value=1e-5)
    set_parameter(device=device, region=region, name="taup", value=1e-5)



def SetSilicaParameters(device, region, T):
    set_parameter(
        device=device, region=region, name="Permittivity", value=eps_si * eps_ox
    )


def CreatePotentialOnly(device, regionSi, regionSiO2):
    """
    Creates the physical models for a Silicon region
    """
    if not InNodeModelList(device, region, "Potential"):
        print("Creating Node Solution Potential")
        CreateSolution(device, region, "Potential")
    elec_i = "n_i*exp(Potential/V_t)"
    hole_i = "n_i^2/IntrinsicElectrons"
    charge_i = "kahan3(IntrinsicHoles, -IntrinsicElectrons, NetDoping)"
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
        CreateNodeModel(device, region, n, e)
        CreateNodeModelDerivative(device, region, n, e, "Potential")

    ### TODO: Edge Average Model
    for i in (
        ("ElectricField", "(Potential@n0-Potential@n1)*EdgeInverseLength"),
        ("PotentialEdgeFlux", "Permittivity * ElectricField"),
    ):
        n = i[0]
        e = i[1]
        CreateEdgeModel(device, region, n, e)
        CreateEdgeModelDerivatives(device, region, n, e, "Potential")

    equation(
        device=device,
        region=region,
        name="PotentialEquation",
        variable_name="Potential",
        node_model="PotentialIntrinsicCharge",
        edge_model="PotentialEdgeFlux",
        variable_update="log_damp",
    )



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

#Parametros del Silicio
T      = 300 # K
SetSiliconParameters(device, core, T)
#Parametros del SiO2
SetSilicaParameters(device, region, T)

Si_ehp = 10e7
SiO2_ehp =10e5

#Electron hole pairs in Silicon se deben hacer con Create Node Model??????
CreateNodeModel(device, region, "Acceptors", "Si_doping")
CreateNodeModel(device, region, "Donors", "Si_doping")
CreateNodeModel(device, region, "NetDoping", "Donors-Acceptors")

print_node_values(device=device, region=region, name="NetDoping")


#Initial Solution 

CreateSolution(device, region, "Potential")

#Poisson
CreatePotentialOnly(device,core, region)





