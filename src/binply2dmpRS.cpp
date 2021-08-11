/////////////////////////////////////////////////////////////////////////
// ---------------- MODIFIED AT 2021/04/30 BY LYWANG ----------------- //
// ------------------------- OPENMP VERSION -------------------------- //
//   FOR CONVERTING [.PLY] TO [.DMP] FILE WITH CAMARA POSE .pose.txt   //
//   WHICH IS A NEW FORMAT FOR STORING 2D DEPTH MAP.                   //
//   USING FACES IN [.PLY] TO PRODUCE DEPTH MAPS WITH HIGHER ACCURACY  //
/////////////////////////////////////////////////////////////////////////
// ---------------- MODIFIED AT 2021/06/10 BY LYWANG ----------------- //
// ----------------------- OPTIMIZED VERSION ------------------------- //
/////////////////////////////////////////////////////////////////////////

#include <omp.h>
#include "sensorData.h"
#include <dirent.h>
#include <string>
#include <vector>
#include <limits>
#include <cstring>
#include <math.h>
#define PAUSE printf("Press Enter key to continue..."); fgetc(stdin);  

using namespace std;
	
const int width = 450;
const int height = 350;
// const double fx = 500;
// const double fy = 500;
// const double cx = 225;
// const double cy = 175;
// const double fx = 192.3265;
// const double fy = 192.3265;

// REALSENSE
// const double fx = 500;
// const double fy = 500;
// const double cx = 260;
// const double cy = 155;

// const double fx = 480;
// const double fy = 480;
// const double cx = 260;
// const double cy = 155;

// REALSENSE-PMD JOINT CALIBRATED
const double fx = 500;
const double fy = 500;
const double cx = 225;
const double cy = 175;

// const double cx = 159.2588;
// const double cy = 120.9104;


class CloudPoint {
public:
	CloudPoint(){
		x = 0;
		y = 0;
		z = 0;
		r = 0;
		g = 0;
		b = 0;
		a = 0;
	}
	CloudPoint(double x, double y, double z, uint8_t r, uint8_t g, uint8_t b, double a)
		:x(x), y(y), z(z), r(r), g(g), b(b), a(a){}
	struct 
	{
		double x, y, z;
		uint8_t r, g, b;
		double a;  // amplitude
	};
};

inline double sign (CloudPoint p1, CloudPoint p2, CloudPoint p3);
inline bool pointInTriangle (CloudPoint pt, CloudPoint v1, CloudPoint v2, CloudPoint v3);
inline double interpolateDepth(CloudPoint pt, CloudPoint v0, CloudPoint v1, CloudPoint v2);
bool pointCompare(CloudPoint a, CloudPoint b);
bool gluInvertMatrix(const double m[16], double invOut[16]);
vector<CloudPoint> transformPointsByPose(vector<CloudPoint> &points);
void readPly(string inFile, vector<CloudPoint> &points, vector<vector<int>> &faces, vector<vector<int>> &face_points);
void histogramEq(ml::vec3uc *colorMap);
// FOR DMP
void convertPlyToDmp(string inFile, string outFile);
void convertAndWriteRDFrame(ofstream &out, vector<CloudPoint> &points, vector<vector<int>> &faces, vector<vector<int>> &face_points);
// MAIN ----------------------------------------------------
int main(int argc, char* argv[])
{
	try {
		//non-cached read
		std::string inFile = "lab05.ply";
		// std::string posePath = "pose_lab05";
		std::string outFile = "lab05.ply.GT.dmp";
		if (argc >= 2) inFile = std::string(argv[1]);
		// else {
		// 	std::cout << "run ./binply2dmp <dir/of/plys> <dir/of/pose> ";
		// 	std::cout << "type in <dir/of/plys> manually: ";
		// 	std::cin >> inFile;
		// 	std::cout << "type in <dir/of/pose> manually: ";
		// 	std::cin >> posePath;
		// }
		// if (argc == 3) {
		// 	posePath = std::string(argv[2]);
		// }
		
		outFile = inFile + ".RS.dmp";
		// if (posePath[posePath.size()-1] != '/') posePath += '/';
		std::cout << "inFile =\t" << inFile << std::endl;
		// std::cout << "posePath =\t" << posePath << std::endl;
		std::cout << "outFile =\t" << outFile << std::endl;

		/////////////////////////////////////////////////////////////////////////
		// Get all POSE.txt files
		
		// DIR *dir;
		// struct dirent *ent;
		// vector<string> poseFiles;
		// if ((dir = opendir (posePath.c_str())) != NULL) {
		// 	/* print all the poseFiles and directories within directory */
		// 	while ((ent = readdir (dir)) != NULL) {
		// 		if(ent->d_name[0] != '.'){
		// 			string file_path = posePath + ent->d_name;
		// 			if (file_path.find(".pose.txt") != string::npos){
		// 				poseFiles.push_back(file_path);
		// 			}
		// 		}
		// 	}
		// 	closedir (dir);
		// } else {
		// 	/* could not open directory */
		// 	perror ("");
		// 	return EXIT_FAILURE;
		// }

		// for(int i=0; i<files.size(); i++){
		// 	string file = files[i];
		// 	printf("%s\n", file.c_str());
		// }

		/////////////////////////////////////////////////////////////////////////
		// sort(poseFiles.begin(), poseFiles.end());
		// std::cout << "loading from files... \n";
		// convertPlyToDmp(inFile, outFile, poseFiles);
		convertPlyToDmp(inFile, outFile);
		//////////////////////////////////////////////////////////////////////
		std::cout << "done!" << std::endl;
		std::cout << std::endl;
	}
	catch (const std::exception& e)
	{
		std::cout << "Exception caught! " << e.what() << std::endl;
		exit(EXIT_FAILURE);
	}
	catch (...)
	{
		std::cout << "Exception caught! (unknown)";
		exit(EXIT_FAILURE);
	}
	
	std::cout << "All done :)" << std::endl;
	return 0;
}

// FUNCTIONS -------------------------------------------------------------
inline double sign (CloudPoint p1, CloudPoint p2, CloudPoint p3){
    return (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y);
}

inline bool pointInTriangle (CloudPoint pt, CloudPoint v1, CloudPoint v2, CloudPoint v3){
    double d1, d2, d3;
    bool has_neg, has_pos;

    d1 = sign(pt, v1, v2);
    d2 = sign(pt, v2, v3);
    d3 = sign(pt, v3, v1);

    has_neg = (d1 < 0) || (d2 < 0) || (d3 < 0);
    has_pos = (d1 > 0) || (d2 > 0) || (d3 > 0);

    return !(has_neg && has_pos);
}

inline double interpolateDepth(CloudPoint pt, CloudPoint v0, CloudPoint v1, CloudPoint v2){
	double x0 = v0.x; double x1 = v1.x; double x2 = v2.x;
	double y0 = v0.y; double y1 = v1.y; double y2 = v2.y;
	double d0 = v0.z; double d1 = v1.z; double d2 = v2.z;
	double xc = pt.x; double yc = pt.y;

	double n0 = d2*(y1-y0) + d0*(y2-y1) + d1*(y0-y2);
	double n2 = y2*(x1-x0) + y0*(x2-x1) + y1*(x0-x2);
	double w3 = yc*(x1-x0) + y0*(xc-x1) + y1*(x0-xc);
	double h = -d0*(yc-y1) - d1*(y0-yc);
	double dc = (n0*w3/n2 + h) / (y1-y0);

	return dc;
}

bool pointCompare(CloudPoint a, CloudPoint b){
	if (a.x == b.x) return a.y < b.y;
    return a.x < b.x;
}

bool gluInvertMatrix(const double m[16], double invOut[16]){
    double inv[16], det;
    int i;

    inv[0] = m[5]  * m[10] * m[15] - 
             m[5]  * m[11] * m[14] - 
             m[9]  * m[6]  * m[15] + 
             m[9]  * m[7]  * m[14] +
             m[13] * m[6]  * m[11] - 
             m[13] * m[7]  * m[10];

    inv[4] = -m[4]  * m[10] * m[15] + 
              m[4]  * m[11] * m[14] + 
              m[8]  * m[6]  * m[15] - 
              m[8]  * m[7]  * m[14] - 
              m[12] * m[6]  * m[11] + 
              m[12] * m[7]  * m[10];

    inv[8] = m[4]  * m[9] * m[15] - 
             m[4]  * m[11] * m[13] - 
             m[8]  * m[5] * m[15] + 
             m[8]  * m[7] * m[13] + 
             m[12] * m[5] * m[11] - 
             m[12] * m[7] * m[9];

    inv[12] = -m[4]  * m[9] * m[14] + 
               m[4]  * m[10] * m[13] +
               m[8]  * m[5] * m[14] - 
               m[8]  * m[6] * m[13] - 
               m[12] * m[5] * m[10] + 
               m[12] * m[6] * m[9];

    inv[1] = -m[1]  * m[10] * m[15] + 
              m[1]  * m[11] * m[14] + 
              m[9]  * m[2] * m[15] - 
              m[9]  * m[3] * m[14] - 
              m[13] * m[2] * m[11] + 
              m[13] * m[3] * m[10];

    inv[5] = m[0]  * m[10] * m[15] - 
             m[0]  * m[11] * m[14] - 
             m[8]  * m[2] * m[15] + 
             m[8]  * m[3] * m[14] + 
             m[12] * m[2] * m[11] - 
             m[12] * m[3] * m[10];

    inv[9] = -m[0]  * m[9] * m[15] + 
              m[0]  * m[11] * m[13] + 
              m[8]  * m[1] * m[15] - 
              m[8]  * m[3] * m[13] - 
              m[12] * m[1] * m[11] + 
              m[12] * m[3] * m[9];

    inv[13] = m[0]  * m[9] * m[14] - 
              m[0]  * m[10] * m[13] - 
              m[8]  * m[1] * m[14] + 
              m[8]  * m[2] * m[13] + 
              m[12] * m[1] * m[10] - 
              m[12] * m[2] * m[9];

    inv[2] = m[1]  * m[6] * m[15] - 
             m[1]  * m[7] * m[14] - 
             m[5]  * m[2] * m[15] + 
             m[5]  * m[3] * m[14] + 
             m[13] * m[2] * m[7] - 
             m[13] * m[3] * m[6];

    inv[6] = -m[0]  * m[6] * m[15] + 
              m[0]  * m[7] * m[14] + 
              m[4]  * m[2] * m[15] - 
              m[4]  * m[3] * m[14] - 
              m[12] * m[2] * m[7] + 
              m[12] * m[3] * m[6];

    inv[10] = m[0]  * m[5] * m[15] - 
              m[0]  * m[7] * m[13] - 
              m[4]  * m[1] * m[15] + 
              m[4]  * m[3] * m[13] + 
              m[12] * m[1] * m[7] - 
              m[12] * m[3] * m[5];

    inv[14] = -m[0]  * m[5] * m[14] + 
               m[0]  * m[6] * m[13] + 
               m[4]  * m[1] * m[14] - 
               m[4]  * m[2] * m[13] - 
               m[12] * m[1] * m[6] + 
               m[12] * m[2] * m[5];

    inv[3] = -m[1] * m[6] * m[11] + 
              m[1] * m[7] * m[10] + 
              m[5] * m[2] * m[11] - 
              m[5] * m[3] * m[10] - 
              m[9] * m[2] * m[7] + 
              m[9] * m[3] * m[6];

    inv[7] = m[0] * m[6] * m[11] - 
             m[0] * m[7] * m[10] - 
             m[4] * m[2] * m[11] + 
             m[4] * m[3] * m[10] + 
             m[8] * m[2] * m[7] - 
             m[8] * m[3] * m[6];

    inv[11] = -m[0] * m[5] * m[11] + 
               m[0] * m[7] * m[9] + 
               m[4] * m[1] * m[11] - 
               m[4] * m[3] * m[9] - 
               m[8] * m[1] * m[7] + 
               m[8] * m[3] * m[5];

    inv[15] = m[0] * m[5] * m[10] - 
              m[0] * m[6] * m[9] - 
              m[4] * m[1] * m[10] + 
              m[4] * m[2] * m[9] + 
              m[8] * m[1] * m[6] - 
              m[8] * m[2] * m[5];

    det = m[0] * inv[0] + m[1] * inv[4] + m[2] * inv[8] + m[3] * inv[12];

    if (det == 0)
        return false;

    det = 1.0 / det;

    for (i = 0; i < 16; i++)
        invOut[i] = inv[i] * det;

    return true;
}

vector<CloudPoint> transformPointsByPose(vector<CloudPoint> &points){
	// ifstream ifs(poseFile, ios::in);

	double p[16] = {1, 0, 0, 0,
					0, -1, 0, 0,
					0, 0, -1, 0,
					0, 0, 0, 1
					};

	// double TK[16] = {1, 0, 0, 0,
	// 			0, 1, 0, 0,
	// 			0, 0, 1, 0,
	// 			0, 0, 0, 1
	// 			};

	// EE09
	double TK[16] = {
	0.9958509144127838, 0.03959186572724391, -0.08193558708801743,  0.050594046652373087, 
	-0.03746839805294778, 0.9989249952393331, 0.027294194134362224, 0.080609482970449813, 
	0.08292813401113083, -0.024110952995148812, 0.9962638137236027, -0.05008868406160092, 
	0.0, 0.0, 0.0, 1.0 };

	// EE06
	// double TK[16] = {
	// 0.9958509144127838, 0.03959186572724391, -0.08193558708801743,  0.020594046652373087, 
	// -0.03746839805294778, 0.9989249952393331, 0.027294194134362224, 0.030609482970449813, 
	// 0.08292813401113083, -0.024110952995148812, 0.9962638137236027, -0.00008868406160092, 
	// 0.0, 0.0, 0.0, 1.0 };

	// EE04
	// double TK[16] = {
	// 0.9958509144127838, 0.03959186572724391, -0.08193558708801743,  0.040594046652373087, 
	// -0.03746839805294778, 0.9989249952393331, 0.027294194134362224, 0.020609482970449813, 
	// 0.08292813401113083, -0.024110952995148812, 0.9962638137236027, -0.00008868406160092, 
	// 0.0, 0.0, 0.0, 1.0 };

	// EE03
	// double TK[16] = {
	// 0.9958509144127838, 0.03959186572724391, -0.08193558708801743,  0.010594046652373087, 
	// -0.03746839805294778, 0.9989249952393331, 0.027294194134362224, 0.020609482970449813, 
	// 0.08292813401113083, -0.024110952995148812, 0.9962638137236027, -0.01008868406160092, 
	// 0.0, 0.0, 0.0, 1.0 };

	// EE08
	// double TK[16] = {
	// 0.9958509144127838, 0.03959186572724391, -0.08193558708801743,  0.031594046652373087, 
	// -0.03746839805294778, 0.9989249952393331, 0.027294194134362224, 0.023609482970449813, 
	// 0.08292813401113083, -0.024110952995148812, 0.9962638137236027, -0.04008868406160092, 
	// 0.0, 0.0, 0.0, 1.0 };

	// EE11
	// double TK[16] = {
	// 0.9958509144127838, 0.03959186572724391, -0.08193558708801743, 0.045594046652373087, 
	// -0.03746839805294778, 0.9989249952393331, 0.027294194134362224, 0.033609482970449813, 
	// 0.08292813401113083, -0.024110952995148812, 0.9962638137236027, 0.02708868406160092, 
	// 0.0, 0.0, 0.0, 1.0 };

	// EE07
	// double TK[16] = {
	// 0.9958509144127838, 0.03959186572724391, -0.08193558708801743, 0.030594046652373087, 
	// -0.03746839805294778, 0.9989249952393331, 0.027294194134362224, 0.013609482970449813, 
	// 0.08292813401113083, -0.024110952995148812, 0.9962638137236027, 0.02708868406160092, 
	// 0.0, 0.0, 0.0, 1.0 };
	
	// EE02
	// double TK[16] = {
	// 0.9958509144127838, 0.03959186572724391, -0.08193558708801743, 0.024594046652373087, 
	// -0.03746839805294778, 0.9989249952393331, 0.027294194134362224, 0.0256609482970449813, 
	// 0.08292813401113083, -0.024110952995148812, 0.9962638137236027, -0.00208868406160092, 
	// 0.0, 0.0, 0.0, 1.0 };

	// // EE000
	// double TK[16] = {
	// 0.9958509144127838, 0.03959186572724391, -0.08193558708801743, 0.024594046652373087, 
	// -0.03746839805294778, 0.9989249952393331, 0.027294194134362224, 0.0016609482970449813, 
	// 0.08292813401113083, -0.024110952995148812, 0.9962638137236027, 0.02708868406160092, 
	// 0.0, 0.0, 0.0, 1.0 };
	
	// RS01F
	// double TK[16] = {
	// 	0.9881869183953346, -0.08094254241783096, -0.1301342350777477, -0.0301103097360968, 
	// 	0.0680661321052437, 0.9926034750692728, -0.10052533481981024, 0.0434185857216809, 
	// 	0.13730847014137376, 0.09048008680003067, 0.986387215002351, 0.10761172949588299, 
	// 	0.0, 0.0, 0.0, 1.0 };
// tx=-0.0371103097360968
// tz=0.10361172949588299


	// for (int i=0; i<16; i++){
	// 	ifs >> p[i];
	// }
	// double p_inv[16];
	// gluInvertMatrix(p, p_inv);

	vector<CloudPoint> resPoints; // transformed points
	for (int i=0; i<points.size(); i++){
		CloudPoint tp = points[i];
		double tx = tp.x;
		double ty = tp.y;
		double tz = tp.z;

		
		// cout << tx << " ";
		// cout << ty << " ";
		// cout << tz << "\n";
		
		double rx = p[0]*tx + p[1]*ty + p[2]*tz + p[3];
		double ry = p[4]*tx + p[5]*ty + p[6]*tz + p[7];
		double rz = p[8]*tx + p[9]*ty + p[10]*tz + p[11];
		
		double rrx = TK[0]*rx + TK[1]*ry + TK[2]*rz + TK[3];
		double rry = TK[4]*rx + TK[5]*ry + TK[6]*rz + TK[7];
		double rrz = TK[8]*rx + TK[9]*ry + TK[10]*rz + TK[11];
		// // rrz = rrz/4;
		
		// cout << rrx << " ";
		// cout << rry << " ";
		// cout << rrz << "\n";
		// PAUSE

		CloudPoint px = CloudPoint(rrx, rry, rrz, tp.r, tp.g, tp.b, 0);
		resPoints.push_back(px);
	}
	
	return resPoints;
}

void readPly(string inFile, vector<CloudPoint> &points, vector<vector<int>> &faces, vector<vector<int>> &face_points){
	ifstream ifs(inFile, ios::binary);

	//////////////////////////////////////////////////////
	// parse header
	char c;
	int counter = 0;
	while ((c = ifs.get()) != EOF) {
		// cout << c << " ";
		if (c == '\n') counter++;
		if (counter == 3) break;
	}
	// PAUSE
	counter = 0;
	while ((c = ifs.get()) != EOF) {
		// cout << c << " ";
		if (c == ' ') counter++;
		if (counter == 2) break;
	}
	
	// PAUSE
	//////////////////////////////////////////////////////
	// parse the number of points
	string s;
	while ((c = ifs.get()) != EOF) {
		// cout << c << " ";
		if (c == '\n') break;
		s += c;		
	}
	// PAUSE
	counter = 0;
	while ((c = ifs.get()) != EOF) {
		// cout << c << " ";
		if (c == '\n') counter++;
		if (counter == 6) break;
	}
	// PAUSE
	counter = 0;
	while ((c = ifs.get()) != EOF) {
		// cout << c << " ";
		if (c == ' ') counter++;
		if (counter == 2) break;
	}
	// PAUSE
	//////////////////////////////////////////////////////
	// parse element face
	string s_face;
	while ((c = ifs.get()) != EOF) {
		// cout << c << " ";
		if (c == '\n') break;
		s_face += c;		
	}
	counter = 0;
	while ((c = ifs.get()) != EOF) {
		// cout << c << " ";
		if (c == '\n') counter++;
		if (counter == 2) break;
	}
	// PAUSE
	// PAUSE
	/////////////////////////////////////////////////
	// START WRITE PLY FILE FOR SENSREADER //////////
	/////////////////////////////////////////////////
	// ofstream pout;
  	// pout.open ("test.ply");
  	// pout << "ply\nend_header\n";
	
	
	/////////////////////////////////////////////////

	int n_point = stoi(s);
	cout << "num of points: " << n_point << '\n';
	int n_face = stoi(s_face);
	cout << "num of faces: " << n_face << '\n';
	//////////////////////////////////////////////////////
	// parsing payload POINTS
	for (int i = 0; i < n_point; i++) {
		if (!ifs.good()) break;
		float x, y, z;
		uint8_t cr, cg, cb, ca;
		ifs.read((char *) &x, sizeof(float));
		ifs.read((char *) &y, sizeof(float));
		ifs.read((char *) &z, sizeof(float));
		ifs.read((char *) &cr, sizeof(char));
		ifs.read((char *) &cg, sizeof(char));
		ifs.read((char *) &cb, sizeof(char));
		// ifs.read((char *) &ca, sizeof(char));
		// cout << (float)x << "\n";
		// cout << (float)y << "\n";
		// cout << (float)z << "\n";
		// cout << (int)cr << "\n";
		// cout << (int)cg << "\n";
		// cout << (int)cb << "\n";
		
		// pout << (float)x << " ";
		// pout << (float)-y << " ";
		// pout << (float)-z << " ";
		// pout << 0 << " ";
		// pout << (int)cr << " ";
		// pout << (int)cg << " ";
		// pout << (int)cb << " \n";
		// cout << (int)ca << "\n";
		// PAUSE
		points.push_back(CloudPoint(x, y, z, cr, cg, cb, 0));

		// initialize #n_point empty vectors in face_points
		vector<int> p;
		face_points.push_back(p);
	}
	
  	// pout.close();
	// printf("test.ply OK.");
	// PAUSE

	//////////////////////////////////////////////////////
	// parsing payload FACES
	for (int i = 0; i < n_face; i++) {
		if (!ifs.good()) break;
		uint8_t n_vertex;
		int fc0, fc1, fc2;
		ifs.read((char *) &n_vertex, sizeof(char));
		ifs.read((char *) &fc0, sizeof(int));
		ifs.read((char *) &fc1, sizeof(int));
		ifs.read((char *) &fc2, sizeof(int));
		vector<int> fc;
		fc.push_back(fc0);
		fc.push_back(fc1);
		fc.push_back(fc2);
		faces.push_back(fc);
		face_points[fc0].push_back(i);
		face_points[fc1].push_back(i);
		face_points[fc2].push_back(i);
		// cout << (int)n_vertex << "\n";
		// cout << (int)fc0 << "\n";
		// cout << (int)fc1 << "\n";
		// cout << (int)fc2 << "\n";
		if(n_vertex != 3){
			cout << "!!!!!!!!!!!!!!!!!" << "\n";
			cout << i << "\n";
			cout << (int)n_vertex << "\n";
			PAUSE
		}
		// points.push_back(CloudPoint(x, y, z, 0));
	}

	// PAUSE
	ifs.close();
}

void histogramEq(ml::vec3uc *colorMap){
	const int MN = width*height;
	int nk[255] = {0};
	for (int i=0; i<MN; i++){
		unsigned char color[3];
		memcpy(&color, colorMap+i, sizeof(ml::vec3uc));
		nk[color[0]]++;
	}
	int nk_acc[255] = {0};
	nk_acc[0] = nk[0];
	unsigned char target[255] = {0}; // 對照表
	for (int i=1; i<255; i++){
		nk_acc[i] = nk_acc[i-1] + nk[i];
		double pk = (double)(nk_acc[i]) * 255/MN;
		int pk_round = (int)(pk + 0.5);
		target[i] = (unsigned char)pk_round;
		// printf("%d\n", pk_round);
	}
	// printf("-----------------------\n");
	// PAUSE
	for (int i=0; i<MN; i++){
		unsigned char color[3];
		memcpy(&color, colorMap+i, sizeof(ml::vec3uc));
		unsigned char n_color = target[color[0]];
		color[0] = color[1] = color[2] = n_color;
		memcpy(colorMap+i, &color, sizeof(ml::vec3uc));
	}
	// PAUSE
}

// FOR DMP ---------------------------------------------------------------
void convertPlyToDmp(string inFile, string outFile){
	ofstream out(outFile, ios::binary);
	if (!out) {
		throw runtime_error("Unable to open file for writing: " + outFile);
	}
	// WRITE HEADER --------------------------------------------------
	char checkFlag[] = "_dmp_yee_";
	// uint32_t n_frame = poseFiles.size();
	uint32_t n_frame = 1;
	uint32_t w_width = width;
	uint32_t w_height = height;
	out.write((const char *) &checkFlag, sizeof(checkFlag));
	out.write((const char *) &n_frame, sizeof(uint32_t));
	out.write((const char *) &w_width, sizeof(uint32_t));
	out.write((const char *) &w_height, sizeof(uint32_t));

	// WRITE DATA -----------------------------------------------------
	vector<CloudPoint> points;
	vector< vector<int> > faces;
	vector< vector<int> > face_points;
	readPly(inFile, points, faces, face_points);
	// for(int i=0; i<poseFiles.size(); i++){
		// if (i == n_frame) break;
		// string poseFile = poseFiles[i];
		// printf("\rConverting [%s] ... [%d/%d]", poseFile.c_str(), i+1, (int)(poseFiles.size()));
		// fflush(stdout);
		vector<CloudPoint> cur_points;
		cur_points = transformPointsByPose(points);
		convertAndWriteRDFrame(out, cur_points, faces, face_points);
	// }
	printf("\n");
	out.close();

	// TRY TO READ FILE -----------------------------------------------
	ifstream rf(outFile, ios::binary);
	if (!rf) {
		cout << "Cannot open file!" << endl;
		exit(1);
   	}
	char flag[10];
	uint32_t n_frame_r;
	uint32_t r_width;
	uint32_t r_height;
	rf.read((char *) &flag, sizeof(flag));
	rf.read((char *) &n_frame_r, sizeof(uint32_t));
	rf.read((char *) &r_width, sizeof(uint32_t));
	rf.read((char *) &r_height, sizeof(uint32_t));
	printf("%s\n", flag);
	printf("%u\n", n_frame_r);
	printf("%u\n", r_width);
	printf("%u\n", r_height);

	// for (int i=0; i<n_frame_r; i++){
	// 	uint8_t *colorMap = new uint8_t[width*height];
	// 	float *depthMap = new float[width*height];
	// 	rf.read((char *) depthMap, sizeof(float)*width*height);
	// 	rf.read((char *) colorMap, sizeof(uint8_t)*width*height);

	// 	for (int iw=0; iw<width; iw++){ // w=450
	// 		for (int ih=0; ih<height; ih++){ // h=350
	// 			uint8_t w_red = colorMap[ih*width + iw];
	// 			float w_depth = depthMap[ih*width + iw];
	// 			printf("%d\n", (int)w_red);
	// 			printf("%f\n", w_depth);
	// 			PAUSE
	// 		}
	// 	}
	// 	delete [] colorMap, depthMap;
	// }

	rf.close();
	exit(0);
}

void convertAndWriteRDFrame(ofstream &out, vector<CloudPoint> &points, vector<vector<int>> &faces, vector<vector<int>> &face_points){
	vector<CloudPoint> projectedPoints; // project 3D points to a 2D plane
	for (int i=0; i<points.size(); i++){
		CloudPoint tp = points[i];
		double tx = tp.x;
		double ty = tp.y;
		double tz = tp.z;
		// perspective
		tx = tx*fx / tz;
		ty = ty*fy / tz;
		
		// for drawing png
		tx = (tx + cx); 
		ty = (ty + cy); 

		// ty = height - (ty + cy); 

		CloudPoint px = CloudPoint(tx, ty, tz, tp.r, tp.g, tp.b, tp.a);
		projectedPoints.push_back(px);
	}

	// nearest neighbor // float32
	uint8_t *colorMap = new uint8_t[width*height*3];
	float *depthMap = new float[width*height];
	memset(colorMap, 0, sizeof(uint8_t)*width*height*3);
	memset(depthMap, 0, sizeof(float)*width*height);
	
	
	double gr = 2; // grid radius 
	// FIND POINTS NEAR THE CENTER OF EACH EACH PIXEL
	vector<int> *neighborPointIds = new vector<int>[width*height];
	for (int i=0; i<projectedPoints.size(); i++){
		CloudPoint p = projectedPoints[i];
		// which pixels are the neighbors of this point
		int lower_x = floor(p.x - gr);
		int upper_x = ceil(p.x + gr);
		int lower_y = floor(p.y - gr);
		int upper_y = ceil(p.y + gr);
		for (int ix=lower_x; ix<=upper_x; ix++){
			for (int iy=lower_y; iy<=upper_y; iy++){
				if (ix < 0 || ix >= width || iy < 0 || iy >= height) continue;
				neighborPointIds[iy*width + ix].push_back(i);
			}
		}
	}

	#pragma omp parallel for
	for (int ih=0; ih<height; ih++){ // h=350
		for (int iw=0; iw<width; iw++){ // w=450
			// printf("[%d][%d]\n", ih, iw);
			CloudPoint nearestPoint = CloudPoint();
			
			vector<int> candiPointIds = neighborPointIds[ih*width + iw];
			vector<int> candiFaces;
			candiFaces.empty();
			int n_candiPoint = 0;

			double MXSqrDist = 9;
			double curSqrDist = MXSqrDist;

			// neighor points of this pixel
			for (auto& pointId : candiPointIds){
				// all faces include this point is taken into account
				for (auto& faceId : face_points[pointId]){
					candiFaces.push_back(faceId);
				}
			}

			std::sort(candiFaces.begin(), candiFaces.end());
			candiFaces.erase(std::unique(candiFaces.begin(), candiFaces.end()), candiFaces.end());
			
			///////////////////////////////////////////////////////////////////////////
			// check if the center of grid lies in any faces(triangles) in candiFaces
			CloudPoint grid_center = CloudPoint((double)iw, (double)ih, 0, 0, 0, 0, 0);
			double minD = 1000;
			for (auto& faceId : candiFaces){
				int v0_id = faces[faceId][0];
				int v1_id = faces[faceId][1];
				int v2_id = faces[faceId][2];
				CloudPoint v0 = projectedPoints[v0_id];
				CloudPoint v1 = projectedPoints[v1_id];
				CloudPoint v2 = projectedPoints[v2_id];
				// cout << "FACE["<<faceId<<"]\n";
				// cout << "("<<v0.x<<", "<<v0.y<<")\n";
				// cout << "("<<v1.x<<", "<<v1.y<<")\n";
				// cout << "("<<v2.x<<", "<<v2.y<<")\n";
				// PAUSE
				// Find intersection
				if (pointInTriangle(grid_center, v0, v1, v2)){
					double d = interpolateDepth(grid_center, v0, v1, v2);
					if (d < minD){
						// // try to find the smallest depth value
						// cout << "------------------[find depth]------------------\n";
						// cout << "("<<v0.x<<", "<<v0.y<<", "<<v0.z<<")\n";
						// cout << "("<<v1.x<<", "<<v1.y<<", "<<v1.z<<")\n";
						// cout << "("<<v2.x<<", "<<v2.y<<", "<<v2.z<<")\n";
						// cout << "------D=("<<iw<<", "<<ih<<", "<<d<<")-----------\n";
						// PAUSE
						minD = d;
					}
				}
				
				// Nearest neighbor point (for RGB data)
				for (auto& pId : faces[faceId]){
					CloudPoint p = projectedPoints[pId];
					if (p.x > iw - gr && p.x < iw + gr &&
						p.y > ih - gr && p.y < ih + gr){
						double sqrDistToCenter = (p.x-iw)*(p.x-iw) + (p.y-ih)*(p.y-ih);
						if (sqrDistToCenter < curSqrDist){
							// try to find the nearest point to the pixel center
							curSqrDist = sqrDistToCenter;
							nearestPoint = p;
						}
					}
				}
			}

			if (minD == 1000 && curSqrDist != MXSqrDist){
				// cannot find any intersection of faces
				// using nearest point within the circle around pixel center with radius [gr]
				uint8_t w_red = 0;
				float w_depth = (float)nearestPoint.z;

				// color RGB
				uint8_t r = nearestPoint.r;
				uint8_t g = nearestPoint.g;
				uint8_t b = nearestPoint.b;
				// double a = nearestPoint.a;
				// int i_a = (int)a;
				// i_a = (i_a > 255) ? 225 : i_a;
                // i_a = (i_a < 0) ? 0 : i_a;
				// w_red = (uint8_t)(i_a);

				colorMap[ih*width*3 + iw*3 + 0] = r;
				colorMap[ih*width*3 + iw*3 + 1] = g;
				colorMap[ih*width*3 + iw*3 + 2] = b;
				depthMap[ih*width + iw] = w_depth;

			} else if (minD == 1000 && curSqrDist == MXSqrDist){
				// point NOT found
				// first color R [uint8] and then D [float32]
				float w_depth = 0; // GIVE ZERO WITHOUT MAX
				colorMap[ih*width*3 + iw*3 + 0] = 0;
				colorMap[ih*width*3 + iw*3 + 1] = 0;
				colorMap[ih*width*3 + iw*3 + 2] = 0;
				depthMap[ih*width + iw] = w_depth;
				// cout << "depth: " << w_depth << "\n";

			} else {
				// intersections FOUND
				uint8_t w_red = 0;
				float w_depth = (float)minD;

				// color RGB
				uint8_t r = nearestPoint.r;
				uint8_t g = nearestPoint.g;
				uint8_t b = nearestPoint.b;
				// double a = nearestPoint.a;
				// int i_a = (int)a;
				// i_a = (i_a > 255) ? 225 : i_a;
                // i_a = (i_a < 0) ? 0 : i_a;
				// w_red = (uint8_t)(i_a);

				colorMap[ih*width*3 + iw*3 + 0] = r;
				colorMap[ih*width*3 + iw*3 + 1] = g;
				colorMap[ih*width*3 + iw*3 + 2] = b;
				depthMap[ih*width + iw] = w_depth;

				// cout << "red: " << (int)w_red << "\n";
				// cout << "depth: " << w_depth << "\n";
			}
			// PAUSE
		}
	}


	out.write((const char *) depthMap, sizeof(float)*width*height );
	out.write((const char *) colorMap, sizeof(uint8_t)*width*height*3 );
	// histogramEq(colorMap);

	delete [] colorMap, depthMap;
}
