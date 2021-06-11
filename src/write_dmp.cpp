/////////////////////////////////////////////////////////////////////////
// ---------------- MODIFIED AT 2021/03/25 BY LYWANG ----------------- //
// ------------------------- OPENMP VERSION -------------------------- //
//   FOR CONVERTING [.PLY] TO [.DMP] FILE WHICH IS A NEW FORMAT FOR    //
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
void readPly(string inFile, vector<CloudPoint> &points);
void histogramEq(ml::vec3uc *colorMap);
// FOR DMP
void convertPlyToDmp(vector<string>& inFiles, string outFile);
void convertAndWriteRDFrame(ofstream &out, vector<CloudPoint> &points);

// MAIN ----------------------------------------------------
int main(int argc, char* argv[])
{
	try {
		//non-cached read
		std::string inPath = "scene_00.ply";
		std::string outFile = "scene_00.dmp";
		if (argc >= 2) inPath = std::string(argv[1]);
		else {
			std::cout << "run ./sens <dir/of/plys> <path/to/dmp>";
			std::cout << "type in <dir/of/plys> manually: ";
			std::cin >> inPath;
			std::cout << "type in <path/to/dmp> manually: ";
			std::cin >> outFile;
		}
		if (argc == 3) {
			outFile = std::string(argv[2]);
		}
		
		if (inPath[inPath.size()-1] != '/') inPath += '/';
		std::cout << "inPath =\t" << inPath << std::endl;
		std::cout << "outFile =\t" << outFile << std::endl;


		/////////////////////////////////////////////////////////////////////////
		// Get all .ply files
		
		DIR *dir;
		struct dirent *ent;
		vector<string> files;
		if ((dir = opendir (inPath.c_str())) != NULL) {
			/* print all the files and directories within directory */
			while ((ent = readdir (dir)) != NULL) {
				if(ent->d_name[0] != '.'){
					string file_path = inPath + ent->d_name;
					files.push_back(file_path);
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
		sort(files.begin(), files.end());
		std::cout << "loading from files... \n";
		convertPlyToDmp(files, outFile);
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

void readPly(string inFile, vector<CloudPoint> &points){
	ifstream ifs(inFile, ifstream::in);
	
	while (ifs.good()){
		string s;
		ifs >> s;
		if (s == "end_header") break;
	}

	// parsing payload
	int counter = 0;

	while (ifs.good()) {
		string s;
		ifs >> s;
		if (s == "") break;
		double x, y, z, red;

		if (counter == 0){
			x = atof(s.c_str());
		} else if (counter == 1){
			y = atof(s.c_str());
		} else if (counter == 2){
			z = atof(s.c_str());
		} else if (counter == 3){
			// do nothing
		} else if (counter == 4){
			if (z == 0){
				// exclude the outlier
			} else {
				red = atof(s.c_str());
				points.push_back(CloudPoint(x, y, z, red));
			}
		}
		counter = (counter + 1) % 7;
	}
	
    sort(points.begin(), points.end(), pointCompare);

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
void convertPlyToDmp(vector<string>& inFiles, string outFile){
	ofstream out(outFile, ios::binary);
	if (!out) {
		throw runtime_error("Unable to open file for writing: " + outFile);
	}
	// WRITE HEADER --------------------------------------------------
	char checkFlag[] = "_dmp_yee_";
	uint32_t n_frame = inFiles.size();
	uint32_t w_width = width;
	uint32_t w_height = height;
	out.write((const char *) &checkFlag, sizeof(checkFlag));
	out.write((const char *) &n_frame, sizeof(uint32_t));
	out.write((const char *) &w_width, sizeof(uint32_t));
	out.write((const char *) &w_height, sizeof(uint32_t));

	// WRITE DATA -----------------------------------------------------
	for(int i=0; i<inFiles.size(); i++){
		if (i == n_frame) break;
		string file = inFiles[i];
		printf("\rConverting [%s] ... [%d/%d]", file.c_str(), i+1, (int)(inFiles.size()));
		fflush(stdout);
		vector<CloudPoint> points;
		readPly(file, points);
		convertAndWriteRDFrame(out, points);
	}
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
			const double MXSqrDist = gr*gr*2 + 1; // out of a grid
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
		
			if(curSqrDist > gr*gr*2 + 1){
				// point not found
				// this pixel is set to the farest point
				// first color R [uint8] and then D [float32]
				uint8_t w_red = 0;
				float w_depth = numeric_limits<float>::max();
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