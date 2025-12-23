# -*- coding: utf-8 -*-
"""
Created on Mon Dec 22 15:54:08 2025

@author: anenr
"""

from devsim import *
from devsim.python_packages.model_create import (
    CreateSolution,
    CreateNodeModel,
    CreateNodeModelDerivative,
    CreateEdgeModel,
    CreateEdgeModelDerivatives,
)


device = "Si_Waveguide"
region = "Si"


q = 1.6e-19  # coul
k = 1.3806503e-23  # J/K
#eps_0 = 8.85e-14  # F/cm^2 -> Pasar a micrometro2!!!!
eps_0 = 8.85e-6  # F/µm²

eps_si = 11.1

T      = 300 # K

# -------------------------------------------------
# Mesh
# -------------------------------------------------
create_gmsh_mesh(mesh=device, file="Rectangle_2D_Lines.msh")

add_gmsh_region(mesh=device, gmsh_name="BOX", region=region, material="Si")

add_gmsh_contact(mesh=device, gmsh_name="bot_contact", region=region, material="metal", name="bot" )

add_gmsh_contact( mesh=device, gmsh_name="top_contact", region=region, material="metal", name="top" )

finalize_mesh(mesh=device)
create_device(mesh=device, device=device)



# TODO: make this temperature dependent
#n_i = 1.0e10  # #/cm^3
n_i = 0.01  # #/µm^3

# constant in our approximation
mu_n = 1350 #reviar poco dopados 1350
mu_p = 400 #serian 480


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
set_parameter(device=device, region=region, name="taun", value=3.3e-6) #Estos valores estan mal
set_parameter(device=device, region=region, name="taup", value=4e-6) #Estos valores estan mal

#initial solution 


CreateSolution(device, region, "Potential")
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


for c in ("top", "bot"):
    contact_node_model(
        device=device,
        contact=c,
        name=f"{c}_bc",
        equation=f"Potential - {c}_bias"
    )

    contact_node_model(
        device=device,
        contact=c,
        name=f"{c}_bc:Potential",
        equation="1"
    )

    contact_equation(
        device=device,
        contact=c,
        name="PotentialEquation",
        node_model=f"{c}_bc",
        edge_charge_model="PotentialEdgeFlux",
    )

set_parameter(device=device, name="top_bias", value=2e-7)
set_parameter(device=device, name="bot_bias", value=0.0)


# -------------------------------------------------
# Solve
# -------------------------------------------------
solve(
    type="dc",
    absolute_error=1e-14,
    relative_error=1e-14,
    maximum_iterations=30
)


# -------------------------------------------------
# Output
# -------------------------------------------------
write_devices(file="Si_TID", type="vtk")







