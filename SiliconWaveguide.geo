SetFactory("OpenCASCADE"); // Usar OpenCASCADE para operaciones booleanas

// Parámetros geométricos


Core_hight = 0.22;
Core_width = 0.6;

CladdingUp_hight = 1.0;
CladdingDown_hight = 5.0;

Cladding_width = 5.0;

//Big Simulation Region

Point(1) = {-Cladding_width / 2, - CladdingDown_hight /2, 0};
Point(2) = {Cladding_width / 2 , -CladdingDown_hight /2, 0};
Point(3) = {Cladding_width / 2, CladdingDown_hight/2, 0};
Point(4) = {- Cladding_width / 2, CladdingDown_hight/2, 0};


Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};

// Create two contact for polarization

Physical Line("bot_contact") = {1};
Physical Line("top_contact") = {3};

// Define the name of the region

Curve Loop(10) = {1, 2, 3, 4};
Plane Surface(100) = {10};


// Physical Surface para Devsim

Physical Surface("SiO2") = {100};


//Core Simulation Region



Point(11) = {-Core_width / 2, CladdingDown_hight /2 - CladdingUp_hight - Core_hight, 0};
Point(12) = {Core_width / 2 , CladdingDown_hight /2 - CladdingUp_hight - Core_hight, 0};
Point(13) = {Core_width / 2, CladdingDown_hight/2 - CladdingUp_hight, 0};
Point(14) = {- Core_width / 2, CladdingDown_hight/2 - CladdingUp_hight, 0};

Line(11) = {11, 12};
Line(12) = {12, 13};
Line(13) = {13, 14};
Line(14) = {14, 11};

Curve Loop(21) = {11, 12, 13, 14};
Plane Surface(200) = {21};


// Physical Surface para Devsim

Physical Surface("Si") = {200};


// -----------------------------------------
// MALLA
// -----------------------------------------
Mesh.CharacteristicLengthMax = 0.01;  // tamaño máximo de elementos
Mesh 2;
Mesh.MshFileVersion = 2.2;

// Guardar el archivo
Save "SiliconWaveguide.msh";
