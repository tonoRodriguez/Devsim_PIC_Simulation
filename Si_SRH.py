# -*- coding: utf-8 -*-
"""
Created on Dec 23 2025

Silicon 1um x 1um, intrinsic, TID irradiation
@author: anenr
"""

from devsim import *
from devsim.python_packages.model_create import (
    CreateSolution, CreateNodeModel, CreateNodeModelDerivative,
    CreateEdgeModel, CreateEdgeModelDerivatives
)
from devsim.python_packages.simple_dd import CreateBernoulli, CreateElectronCurrent, CreateHoleCurrent

# -----------------------------
# Device and region
# -----------------------------
device = "Si_Waveguide"
region = "Si"

# Physical constants
q = 1.6e-19       # C
k = 1.3806503e-23 # J/K
eps_0 = 8.85e-6   # F/µm²
eps_si = 11.1
T = 300           # K

# -----------------------------
# Mesh
# -----------------------------
create_gmsh_mesh(mesh=device, file="Rectangle_2D_Lines.msh")
add_gmsh_region(mesh=device, gmsh_name="BOX", region=region, material="Si")
add_gmsh_contact(mesh=device, gmsh_name="bot_contact", region=region, material="metal", name="bot")
add_gmsh_contact(mesh=device, gmsh_name="top_contact", region=region, material="metal", name="top")
finalize_mesh(mesh=device)
create_device(mesh=device, device=device)

# -----------------------------
# Parameters
# -----------------------------
n_i = 0.01   # #/µm³ for intrinsic Si
mu_n = 1350
mu_p = 400

set_parameter(device=device, region=region, name="Permittivity", value=eps_si * eps_0)
set_parameter(device=device, region=region, name="ElectronCharge", value=q)
set_parameter(device=device, region=region, name="n_i", value=n_i)
set_parameter(device=device, region=region, name="T", value=T)
set_parameter(device=device, region=region, name="kT", value=k*T)
set_parameter(device=device, region=region, name="V_t", value=k*T/q)
set_parameter(device=device, region=region, name="mu_n", value=mu_n)
set_parameter(device=device, region=region, name="mu_p", value=mu_p)

# SRH parameters
set_parameter(device=device, region=region, name="n1", value=n_i)
set_parameter(device=device, region=region, name="p1", value=n_i)
set_parameter(device=device, region=region, name="taun", value=3.3e-6)
set_parameter(device=device, region=region, name="taup", value=4e-6)

# -----------------------------
# Poisson initial solution
# -----------------------------
CreateSolution(device, region, "Potential")
elec_i = "n_i*exp(Potential/V_t)"
hole_i = "n_i*exp(-Potential/V_t)"
charge_i = "kahan3(IntrinsicHoles, -IntrinsicElectrons, 0)"
pcharge_i = "-ElectronCharge * IntrinsicCharge"

# Node models for intrinsic carriers
for n, expr in [
    ("IntrinsicElectrons", elec_i),
    ("IntrinsicHoles", hole_i),
    ("IntrinsicCharge", charge_i),
    ("PotentialIntrinsicCharge", pcharge_i),
]:
    CreateNodeModel(device, region, n, expr)
    CreateNodeModelDerivative(device, region, n, expr, "Potential")

# Edge models for E and D
for n, expr in [
    ("ElectricField", "(Potential@n0-Potential@n1)*EdgeInverseLength"),
    ("PotentialEdgeFlux", "Permittivity * ElectricField"),
]:
    CreateEdgeModel(device, region, n, expr)
    CreateEdgeModelDerivatives(device, region, n, expr, "Potential")

# Poisson
equation(
    device=device,
    region=region,
    name="PotentialEquation",
    variable_name="Potential",
    node_model="PotentialIntrinsicCharge",
    edge_model="PotentialEdgeFlux",
    variable_update="log_damp"
)

# Contact boundary conditions for Poisson
for c in ("top", "bot"):
    contact_node_model(device=device, contact=c, name=f"{c}_bc", equation=f"Potential - {c}_bias")
    contact_node_model(device=device, contact=c, name=f"{c}_bc:Potential", equation="1")
    contact_equation(device=device, contact=c, name="PotentialEquation", node_model=f"{c}_bc", edge_charge_model="PotentialEdgeFlux")

# Small applied bias
set_parameter(device=device, name="top_bias", value=2e-7)
set_parameter(device=device, name="bot_bias", value=0.0)

# Solve initial Poisson
solve(type="dc", absolute_error=1e-14, relative_error=1e-14, maximum_iterations=30)

# -----------------------------
# Drift-diffusion solution
# -----------------------------
CreateSolution(device, region, "Electrons")
CreateSolution(device, region, "Holes")

set_node_values(device=device, region=region, name="Electrons", init_from="IntrinsicElectrons")
set_node_values(device=device, region=region, name="Holes", init_from="IntrinsicHoles")

# Poisson coupled to carriers
pne = "-ElectronCharge*kahan3(Holes, -Electrons, 0)"
CreateNodeModel(device, region, "PotentialNodeCharge", pne)
CreateNodeModelDerivative(device, region, "PotentialNodeCharge", pne, "Electrons")
CreateNodeModelDerivative(device, region, "PotentialNodeCharge", pne, "Holes")
equation(device=device, region=region, name="PotentialEquation", variable_name="Potential",
         node_model="PotentialNodeCharge", edge_model="PotentialEdgeFlux", variable_update="log_damp")

# Bernoulli for SG method
CreateBernoulli(device, region)

# -----------------------------
# SRH recombination
# -----------------------------
USRH = "(Electrons*Holes - n_i^2)/(taup*(Electrons + n1) + taun*(Holes + p1))"
CreateNodeModel(device, region, "USRH", USRH)
for n in ("Electrons", "Holes"):
    CreateNodeModelDerivative(device, region, "USRH", USRH, n)

# -----------------------------
# TID generation
# -----------------------------
G_rad_value = 1e-3  # pares/µm³·s, ejemplo
CreateNodeModel(device, region, "G_rad", f"{G_rad_value}")
for n in ("Electrons", "Holes"):
    CreateNodeModelDerivative(device, region, "G_rad", f"{G_rad_value}", n)

# -----------------------------
# Electron continuity
# -----------------------------
CreateElectronCurrent(device, region, "mu_n")
CreateNodeModel(device, region, "ElectronChargeNode", "-ElectronCharge * Electrons")
CreateNodeModelDerivative(device, region, "ElectronChargeNode", "-ElectronCharge * Electrons", "Electrons")


# Node model que combina recombinación SRH + generación TID
CreateNodeModel(device, region, "GenerationTotal", "USRH + G_rad")
for n in ("Electrons", "Holes"):
    CreateNodeModelDerivative(device, region, "GenerationTotal", "USRH + G_rad", n)


equation(
    device=device,
    region=region,
    name="ElectronContinuityEquation",
    variable_name="Electrons",
    time_node_model="ElectronChargeNode",
    edge_model="ElectronCurrent",
    node_model="GenerationTotal",
    variable_update="positive"
)

# Hole continuity
CreateHoleCurrent(device, region, "mu_p")
CreateNodeModel(device, region, "HoleChargeNode", "ElectronCharge * Holes")
CreateNodeModelDerivative(device, region, "HoleChargeNode", "ElectronCharge * Holes", "Holes")

equation(
    device=device,
    region=region,
    name="HoleContinuityEquation",
    variable_name="Holes",
    time_node_model="HoleChargeNode",
    edge_model="HoleCurrent",
    node_model="GenerationTotal",
    variable_update="positive"
)

# Contact BC for carriers (intrinsic)
for c in ("top", "bot"):
    # electrons
    contact_node_model(device=device, contact=c, name=f"{c}_n_bc", equation="Electrons - n_i")
    contact_node_model(device=device, contact=c, name=f"{c}_n_bc:Electrons", equation="1")
    contact_equation(device=device, contact=c, name="ElectronContinuityEquation", node_model=f"{c}_n_bc")

    # holes
    contact_node_model(device=device, contact=c, name=f"{c}_p_bc", equation="Holes - n_i")
    contact_node_model(device=device, contact=c, name=f"{c}_p_bc:Holes", equation="1")
    contact_equation(device=device, contact=c, name="HoleContinuityEquation", node_model=f"{c}_p_bc")

# -----------------------------
# Solve drift-diffusion with TID
# -----------------------------
solve(type="dc", absolute_error=1e-14, relative_error=1e-14, maximum_iterations=50)

# -----------------------------
# Output
# -----------------------------
write_devices(file="Si_TID_DD", type="vtk")



#Datos 
# n_values = get_node_model_values(device=device, region=region, name="Electrons")



