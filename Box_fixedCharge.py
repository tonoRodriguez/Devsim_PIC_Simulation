# -*- coding: utf-8 -*-
"""
SiO2 (BOX) Poisson simulation with fixed charge
"""

from devsim import *
from devsim.python_packages.model_create import (
    CreateSolution,
    CreateNodeModel,
    CreateNodeModelDerivative,
    CreateEdgeModel,
    CreateEdgeModelDerivatives,
)

# -------------------------------------------------
# Constants (units: µm, V, C)
# -------------------------------------------------
q = 1.602e-19           # Coulomb
eps_0 = 8.85e-6         # F / µm
eps_ox = 3.9

device = "BOX_WG"
region = "BOX"

# -------------------------------------------------
# Mesh
# -------------------------------------------------
create_gmsh_mesh(mesh=device, file="Rectangle_2D_Lines.msh")

add_gmsh_region(mesh=device, gmsh_name="BOX", region=region, material="SiO2")

add_gmsh_contact(mesh=device, gmsh_name="bot_contact", region=region, material="metal", name="bot" )

add_gmsh_contact( mesh=device, gmsh_name="top_contact", region=region, material="metal", name="top" )

finalize_mesh(mesh=device)
create_device(mesh=device, device=device)

# -------------------------------------------------
# Parameters
# -------------------------------------------------
set_parameter(
    device=device,
    region=region,
    name="Permittivity",
    value=eps_0 * eps_ox
)

# Fixed oxide charge
# Original: 3.5e16 cm^-3 → µm^-3
set_parameter(
    device=device,
    region=region,
    name="OxideChargeDensity",
    value=3.5e20 * q / 1e12   # C / µm^3
)

# -------------------------------------------------
# Solution
# -------------------------------------------------
CreateSolution(device, region, "Potential")

# -------------------------------------------------
# Fixed charge (Poisson RHS)
# -------------------------------------------------
CreateNodeModel(
    device,
    region,
    "FixedCharge",
    "OxideChargeDensity"
)

CreateNodeModel(
    device,
    region,
    "NodeCharge",
    "-FixedCharge"
)

# d(NodeCharge)/d(Potential) = 0
CreateNodeModelDerivative(
    device,
    region,
    "NodeCharge",
    "0",
    "Potential"
)

# -------------------------------------------------
# Electric field
# -------------------------------------------------
CreateEdgeModel(
    device,
    region,
    "ElectricField",
    "(Potential@n0 - Potential@n1)*EdgeInverseLength"
)

CreateEdgeModelDerivatives(
    device,
    region,
    "ElectricField",
    "(Potential@n0 - Potential@n1)*EdgeInverseLength",
    "Potential"
)

# -------------------------------------------------
# Displacement field: D = εE
# -------------------------------------------------
CreateEdgeModel(
    device,
    region,
    "PotentialEdgeFlux",
    "Permittivity * ElectricField"
)

CreateEdgeModelDerivatives(
    device,
    region,
    "PotentialEdgeFlux",
    "Permittivity * ElectricField",
    "Potential"
)

# -------------------------------------------------
# Poisson equation
# -------------------------------------------------
equation(
    device=device,
    region=region,
    name="PotentialEquation",
    variable_name="Potential",
    node_model="NodeCharge",
    edge_model="PotentialEdgeFlux"
)

# -------------------------------------------------
# Contacts (Dirichlet)
# -------------------------------------------------
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
        node_model=f"{c}_bc"
    )

# Bias
set_parameter(device=device, name="top_bias", value=0.0)
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
write_devices(file="BOX_fixed_charge", type="vtk")

