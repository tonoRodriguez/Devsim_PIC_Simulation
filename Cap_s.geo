SetFactory("OpenCASCADE"); // Usar OpenCASCADE para operaciones booleanas


// Parámetros geométricos


xmin  = 0;
xmax  = 1.0;


ymin  = 0.0;
ymax  = 1.0;


// -----------------------------------------
// RECTÁNGULO GRANDE (AIRE)
// -----------------------------------------
Point(1) = {xmin, ymin, 0};
Point(2) = {xmax, ymin, 0};
Point(3) = {xmax, ymax, 0};
Point(4) = {xmin, ymax, 0};

Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};

Physical Line("bot_contact") = {1};
Physical Line("top_contact") = {3};

Curve Loop(10) = {1, 2, 3, 4};
Plane Surface(100) = {10};


// Physical Surface para Devsim
Physical Surface("BOX") = {100};


// -----------------------------------------
// MALLA
// -----------------------------------------
Mesh.CharacteristicLengthMax = 0.01;  // tamaño máximo de elementos
Mesh 2;
Mesh.MshFileVersion = 2.2;

// Guardar el archivo
Save "Rectangle_2D_Lines.msh";