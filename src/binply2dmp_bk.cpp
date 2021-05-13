/////////////////////////////////////////////////////////////////////////
// ---------------- MODIFIED AT 2021/04/15 BY LYWANG ----------------- //
// ------------------------- OPENMP VERSION -------------------------- //
//   FOR CONVERTING [.PLY] TO [.DMP] FILE WITH CAMARA POSE .pose.txt   //
//   WHICH IS A NEW FORMAT FOR                                         //
//   STORING 2D DEPTH MAP.                                             //
/////////////////////////////////////////////////////////////////////////

#include <omp.h>
#include "sensorData.h"
#include <dirent.h>
#include <string>
#include <vector>
#include <limits>
#define PAUSE printf("Press Enter key to continue..."); fgetc(stdin);  

using namespace std;
	
const int width = 450;
const int height = 350;
const double fx = 500;
const double fy = 500;
const double cx = 225;
const double cy = 175;

class CloudPoint {
public:
	CloudPoint(){
		x = 0;
		y = 0;
		z = 0;
		a = 0;
	}
	CloudPoint(double x, double y, double z, double amp)
		:x(x), y(y), z(z), a(amp){}
	struct 
	{
		double x, y, z;
		double a;  // amplitude
	};
};

bool pointCompare(CloudPoint a, CloudPoint b);
bool gluInvertMatrix(const double m[16], double invOut[16]);
vector<CloudPoint> transformPointsByPose(vector<CloudPoint> &points, string poseFile);
void readPly(string inFile, vector<CloudPoint> &points);
void histogramEq(ml::vec3uc *colorMap);
// FOR DMP
void convertPlyToDmp(string inFile, string outFile, vector<string>& poseFiles);
void convertAndWriteRDFrame(ofstream &out, vector<CloudPoint> &points);
// MAIN ----------------------------------------------------
int main(int argc, char* argv[])
{
	try {
		//non-cached read
		std::string inFile = "lab05.ply";
		std::string posePath = "pose_lab05";
		std::string outFile = "lab05.ply.GT.dmp";
		if (argc >= 2) inFile = std::string(argv[1]);
		else {
			std::cout << "run ./binply2dmp <dir/of/plys> <dir/of/pose> ";
			std::cout << "type in <dir/of/plys> manually: ";
			std::cin >> inFile;
			std::cout << "type in <dir/of/pose> manually: ";
			std::cin >> posePath;
		}
		if (argc == 3) {
			posePath = std::string(argv[2]);
		}
		
		outFile = inFile + ".GT.dmp";
		if (posePath[posePath.size()-1] != '/') posePath += '/';
		std::cout << "inFile =\t" << inFile << std::endl;
		std::cout << "posePath =\t" << posePath << std::endl;
		std::cout << "outFile =\t" << outFile << std::endl;

		/////////////////////////////////////////////////////////////////////////
		// Get all POSE.txt files
		
		DIR *dir;
		struct dirent *ent;
		vector<string> poseFiles;
		if ((dir = opendir (posePath.c_str())) != NULL) {
			/* print all the poseFiles and directories within directory */
			while ((ent = readdir (dir)) != NULL) {
				if(ent->d_name[0] != '.'){
					string file_path = posePath + ent->d_name;
					poseFiles.push_back(file_path);
				}
			}
			closedir (dir);
		} else {
			/* could not open directory */
			perror ("");
			return EXIT_FAILURE;
		}

		// for(int i=0; i<files.size(); i++){
		// 	string file = files[i];
		// 	printf("%s\n", file.c_str());
		// }

		/////////////////////////////////////////////////////////////////////////
		sort(poseFiles.begin(), poseFiles.end());
		std::cout << "loading from files... \n";
		convertPlyToDmp(inFile, outFile, poseFiles);
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

vector<CloudPoint> transformPointsByPose(vector<CloudPoint> &points, string poseFile){
	ifstream ifs(poseFile, ios::in);

	double p[16];
	for (int i=0; i<16; i++){
		ifs >> p[i];
		// cout << p[i] << "\n";
	}
	// cout << "------------------\n";
	double p_inv[16];
	gluInvertMatrix(p, p_inv);
	// for (int i=0; i<16; i++){
	// 	cout << p_inv[i] << "\n";
	// }
	// PAUSE

	vector<CloudPoint> resPoints; // transformed points
	for (int i=0; i<points.size(); i++){
		CloudPoint tp = points[i];
		double tx = tp.x;
		double ty = tp.y;
		double tz = tp.z;
		// cout << tx << "\n";
		// cout << ty << "\n";
		// cout << tz << "\n";
		// cout << "------------------\n";
		double rx = p_inv[0]*tx + p_inv[1]*ty + p_inv[2]*tz + p_inv[3];
		double ry = p_inv[4]*tx + p_inv[5]*ty + p_inv[6]*tz + p_inv[7];
		double rz = p_inv[8]*tx + p_inv[9]*ty + p_inv[10]*tz + p_inv[11];
		// cout << rx << "\n";
		// cout << ry << "\n";
		// cout << rz << "\n";
		// cout << "======================\n\n";
		// PAUSE
		CloudPoint px = CloudPoint(rx, ry, rz, 0);
		resPoints.push_back(px);
	}
	
	return resPoints;
}

void readPly(string inFile, vector<CloudPoint> &points){
	ifstream ifs(inFile, ios::binary);

	//////////////////////////////////////////////////////
	// parse header
	char c;
	int counter = 0;
	while ((c = ifs.get()) != EOF) {
		if (c == '\n') counter++;
		if (counter == 3) break;
	}
	counter = 0;
	while ((c = ifs.get()) != EOF) {
		if (c == ' ') counter++;
		if (counter == 2) break;
	}
	//////////////////////////////////////////////////////
	// parse the number of points
	string s;
	while ((c = ifs.get()) != EOF) {
		if (c == '\n') break;
		s += c;		
	}
	counter = 0;
	while ((c = ifs.get()) != EOF) {
		if (c == '\n') counter++;
		if (counter == 7) break;
	}
	counter = 0;
	while ((c = ifs.get()) != EOF) {
		if (c == ' ') counter++;
		if (counter == 2) break;
	}
	//////////////////////////////////////////////////////
	// parse element face
	string s_face;
	while ((c = ifs.get()) != EOF) {
		if (c == '\n') break;
		s_face += c;		
	}
	counter = 0;
	while ((c = ifs.get()) != EOF) {
		if (c == '\n') counter++;
		if (counter == 2) break;
	}

	int n_point = stoi(s);
	cout << "num of points: " << n_point << '\n';
	int n_face = stoi(s_face);
	cout << "num of faces: " << n_face << '\n';
	PAUSE
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
		ifs.read((char *) &ca, sizeof(char));
		// cout << (double)x << "\n";
		// cout << (float)y << "\n";
		// cout << (float)z << "\n";
		// cout << (int)cr << "\n";
		// cout << (int)cg << "\n";
		// cout << (int)cb << "\n";
		// cout << (int)ca << "\n";
		// PAUSE
		points.push_back(CloudPoint(x, y, z, 0));
	}

    // sort(points.begin(), points.end(), pointCompare);

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
void convertPlyToDmp(string inFile, string outFile, vector<string>& poseFiles){
	ofstream out(outFile, ios::binary);
	if (!out) {
		throw runtime_error("Unable to open file for writing: " + outFile);
	}
	// WRITE HEADER --------------------------------------------------
	char checkFlag[] = "_dmp_yee_";
	uint32_t n_frame = poseFiles.size();
	uint32_t w_width = width;
	uint32_t w_height = height;
	out.write((const char *) &checkFlag, sizeof(checkFlag));
	out.write((const char *) &n_frame, sizeof(uint32_t));
	out.write((const char *) &w_width, sizeof(uint32_t));
	out.write((const char *) &w_height, sizeof(uint32_t));

	// WRITE DATA -----------------------------------------------------
	vector<CloudPoint> points;
	readPly(inFile, points);
	for(int i=0; i<poseFiles.size(); i++){
		if (i == n_frame) break;
		string poseFile = poseFiles[i];
		printf("Converting [%s] ... [%d/%d]\n", poseFile.c_str(), i+1, (int)(poseFiles.size()));
		vector<CloudPoint> cur_points;
		cur_points = transformPointsByPose(points, poseFile);
		convertAndWriteRDFrame(out, cur_points);
	}
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

void convertAndWriteRDFrame(ofstream &out, vector<CloudPoint> &points){
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
		CloudPoint px = CloudPoint(tx, ty, tz, tp.a);
		projectedPoints.push_back(px);
	}

	// nearest neighbor // float32
	uint8_t *colorMap = new uint8_t[width*height];
	float *depthMap = new float[width*height];
	memset(colorMap, 0, sizeof(uint8_t)*width*height);
	memset(depthMap, 0, sizeof(float)*width*height);
	
	#pragma omp parallel for
	for (int iw=0; iw<width; iw++){ // w=450
		for (int ih=0; ih<height; ih++){ // h=350
			// printf("[%d][%d]\n", iw, ih);
			CloudPoint nearestPoint = CloudPoint();
			double gr = 2; // grid radius !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
			double MXSqrDist = gr*gr*2 + 1; // out of a grid
			double curSqrDist = MXSqrDist;
			for (int i=0; i<projectedPoints.size(); i++){
				CloudPoint p = projectedPoints[i];
				// whether the point in 2x2 grid
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
			if(curSqrDist == MXSqrDist){
				gr = 4; // grid radius doubled
				MXSqrDist = gr*gr*2 + 1; // out of a grid
				curSqrDist = MXSqrDist;
				for (int i=0; i<projectedPoints.size(); i++){
					CloudPoint p = projectedPoints[i];
					// whether the point in 2x2 grid
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
			if(curSqrDist == MXSqrDist){
				gr = 8; // grid radius doubled
				MXSqrDist = gr*gr*2 + 1; // out of a grid
				curSqrDist = MXSqrDist;
				for (int i=0; i<projectedPoints.size(); i++){
					CloudPoint p = projectedPoints[i];
					// whether the point in 2x2 grid
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
			if(curSqrDist == MXSqrDist){
				gr = 16; // grid radius doubled
				MXSqrDist = gr*gr*2 + 1; // out of a grid
				curSqrDist = MXSqrDist;
				for (int i=0; i<projectedPoints.size(); i++){
					CloudPoint p = projectedPoints[i];
					// whether the point in 2x2 grid
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



			if(curSqrDist == MXSqrDist){
				// point STILLLLLLLLLL not found
				// this pixel is set to the farest point
				// first color R [uint8] and then D [float32]
				uint8_t w_red = 0;
				// float w_depth = numeric_limits<float>::max();
				float w_depth = 0; // GIVE ZERO WITHOUT MAXXXXXXXXXXXXXXXXXXXX
				colorMap[ih*width + iw] = w_red;
				depthMap[ih*width + iw] = w_depth;
				// cout << "red: " << (int)w_red << "\n";
				// cout << "depth: " << w_depth << "\n";
			} else {
				// found the point in the circle around pixel center with radius [gr]
				// depthMap[ih*width + iw] = (unsigned short)(nearestPoint.z * 1000);
				uint8_t w_red = 0;
				float w_depth = (float)nearestPoint.z;

				// color red
				double a = nearestPoint.a;
				// a = a*3; // 調亮
				int i_a = (int)a;
				i_a = (i_a > 255) ? 225 : i_a;
                i_a = (i_a < 0) ? 0 : i_a;
				w_red = (uint8_t)(i_a);
				colorMap[ih*width + iw] = w_red;
				depthMap[ih*width + iw] = w_depth;

				// cout << "red: " << (int)w_red << "\n";
				// cout << "depth: " << w_depth << "\n";
			}
			// PAUSE
		}
	}


	out.write((const char *) depthMap, sizeof(float)*width*height );
	out.write((const char *) colorMap, sizeof(uint8_t)*width*height );
	// histogramEq(colorMap);

	delete [] colorMap, depthMap;
}