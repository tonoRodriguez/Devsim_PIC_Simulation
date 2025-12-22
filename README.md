# Devsim Project

## About Devsim

Devsim is an open-source TCAD simulator.  
It solves differential equations using the Newton-Raphson method for solving Poisson's equation.  
This method is used for finding a minimum value (root) and searches for solutions of the type required by semiconductor simulations.

---

## Extra Tools Needed

- **Gmesh**: Creates 2D and 3D meshes used by Devsim.  
  [Gmesh Documentation](https://gmsh.info/doc/texinfo/gmsh.html) | [Gmesh Tutorial](https://gmsh.info/doc/texinfo/gmsh.html)
- **VTK**: Visualization tool for writing heat maps from Devsim results.
- **ParaView**: Tool for opening VTK files (VTM and VTU).
- **Python libraries**: numpy, matplotlib, etc.

---

## Physical Models

### Node Models (Nodos)
Variables local to nodes:

- `Potential (φ)`
- `Electrons (n)`
- `Holes (p)`
- `n_i`, `μ_n`, `μ_p`, `V_t`
- SRH: `U_SRH`, `G_total`

### Edge Models (Aristas)
Gradients and fluxes between nodes:

- `ElectricField = (φ@0 - φ@1) / Δx`
- `ElectronCurrent` (drift + diffusion)
- `HoleCurrent` (drift + diffusion)
- `DField = ε * E`
- `∇n`, `∇p` via `edge_from_node_model`

---

## Work Setup in Devsim

1. **Create Mesh**  
   Generate 2D waveguide mesh using Gmesh or Devsim's internal mesh. Define regions and contacts.

2. **Parameter Definition**  
   Define constants and magnitudes for simulation.

3. **Define Solutions**  
   Variables to solve:
   - `Potential` for semiconductor and insulator regions.
   - `Electrons` for semiconductor region.
   - `Holes` for semiconductor region.

4. **Define Doping and Fixed Charges**  
   Example: Oxide trap density and fixed charges as node models.

5. **Silicon Carrier Models**  
   Define parameters like `G_rad` and total charge (`Electrons - Holes`).

6. **Generation and Recombination Models**  
   - Recombination: SRH (`U_SRH`)  
   - Generation due to radiation: Node model  
   - Total generation: Node model

7. **Electric Field Models**  
   Edge models for electric field, electrons, and holes.

8. **Differential Equations**  
   Solved using Newton's method:
   - Potential in SiO2 and Si
   - Electron continuity
   - Hole continuity

9. **Electrical Contacts**  
   Example: `set_contact_bias` for bottom contact (0 V) and top contact (0 V).

10. **Electrostatic Initialization**  
    Solve only Poisson equation using Boltzmann statistics as initial guess.

11. **TID Simulation**  
    Activate `G_rad` and solve DC.

12. **Output**  
    Write device results in VTK format and visualize with ParaView.

---

## Math and Algorithms Used

Devsim solves differential equations in nodes using the Newton-Raphson method:

\[
J(x_k) \Delta x = -F(x_k)
\]

Where `J(x_k)` is the Jacobian. The iterative solution is:

\[
x_{k+1} = x_k + \Delta x
\]

Differential equations are solved at each node.  
Edge fluxes are computed using methods like Scharfetter–Gummel to ensure continuity of currents between nodes.

---

## Table of Key Concepts

| Concept       | Description                                 | Example                     |
| ------------- | ------------------------------------------- | --------------------------- |
| **Solution**  | Variable to solve with the solver           | `Potential`, `Electrons`, `Holes` |
| **NodeModel** | Algebraic expression evaluated at nodes     | `NetDoping`, `Charge`, `G_rad` |
| **EdgeModel** | Expression evaluated on edges               | `ElectricField`, `Current` |

