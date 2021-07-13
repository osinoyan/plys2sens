// ------------ MODIFIED AT 2021/03/18 BY LYWANG ---------------------
// ---------- FOR CONVERTING [.PLY] TO [.SENS] FILE ------------------
// ---------- OPENMP VERSION ------------------
// ------------ MODIFIED AT 2021/06/11 BY LYWANG ---------------------
// ----------------------- OPTIMEZED VERSION -------------------------

#include <omp.h>
#include "sensorData.h"
#include <dirent.h>
#include <string>
#include <vector>
#define _MSC_ ml::SensorData::CalibrationData
#define _MS_ ml::SensorData
#define PAUSE printf("Press Enter key to continue..."); fgetc(stdin);  

using namespace std;
	
const int width = 450;
const int height = 350;
// const int width = 512;
// const int height = 384;
const double fx = 500;
const double fy = 500;
const double cx = 225;
const double cy = 175;

//THIS IS A DEMO FUNCTION: HOW TO DECODE .SENS FILES: CHECK IT OUT! (doesn't do anything real though)
void processFrame(const ml::SensorData& sd, size_t frameIdx) {
	
	//de-compress color and depth values
	ml::vec3uc* colorData = sd.decompressColorAlloc(frameIdx);
	unsigned short* depthData = sd.decompressDepthAlloc(frameIdx);

	//dimensions of a color/depth frame
	sd.m_colorWidth;
	sd.m_colorHeight;
	sd.m_depthWidth;
	sd.m_depthHeight;
	
	for (unsigned int i = 0; i < sd.m_depthWidth * sd.m_depthHeight; i++) {
		//convert depth values to m:
		float depth_in_meters = sd.m_depthShift * depthData[i];
	}

	std::free(colorData);
	std::free(depthData);
}


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
void convertToRGBDFrame(ml::SensorData& sd, vector<CloudPoint> &points);
void convertPlyToSens(vector<string>& inFiles, string outFile, ml::SensorData& sd);

// MAIN ----------------------------------------------------
int main(int argc, char* argv[])
{
#ifdef WIN32
#if defined(DEBUG) | defined(_DEBUG)
	_CrtSetDbgFlag(_CRTDBG_ALLOC_MEM_DF | _CRTDBG_LEAK_CHECK_DF);
#endif
#endif
	try {
		//non-cached read
		std::string inPath = "scene_00.ply";
		std::string outFile = "scene_00.sens";
		if (argc >= 2) inPath = std::string(argv[1]);
		else {
			std::cout << "run ./sens <path/to/plys>";
			std::cout << "type in path manually: ";
			std::cin >> inPath;
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
		ml::SensorData sd = ml::SensorData();
		convertPlyToSens(files, outFile, sd);

		//////////////////////////////////////////////////////////////////////


		std::cout << "done!" << std::endl;

		std::cout << sd << std::endl;

		std::cout << std::endl;
	}
	catch (const std::exception& e)
	{
#ifdef WIN32
		MessageBoxA(NULL, e.what(), "Exception caught", MB_ICONERROR);
#else
		std::cout << "Exception caught! " << e.what() << std::endl;
#endif
		exit(EXIT_FAILURE);
	}
	catch (...)
	{
#ifdef WIN32
		MessageBoxA(NULL, "UNKNOWN EXCEPTION", "Exception caught", MB_ICONERROR);
#else
		std::cout << "Exception caught! (unknown)";
#endif
		exit(EXIT_FAILURE);
	}
	
	std::cout << "All done :)" << std::endl;

#ifdef WIN32
	std::cout << "<press key to continue>" << std::endl;
	getchar();
#endif
	return 0;
}

// FUNCTIONS -----------------------------------------------
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
	double fx = 500;
	double fy = 500;
	// double k1 = 0.000001;

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
			if (x == 0 && y == 0 && z == 0){
				// exclude the outlier
			} else {
				// amp = atof(s.c_str());
				// points.push_back(CloudPoint(x, y, z, amp));
			}
		} else if (counter == 4){
			if (x == 0 && y == 0 && z == 0){
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

void convertToRGBDFrame(ml::SensorData& sd, vector<CloudPoint> &points){
	// compressDepth(const unsigned short* depth, unsigned int width, unsigned int height, COMPRESSION_TYPE_DEPTH type)
	// RGBDFrame& addFrame(const vec3uc* color, const unsigned short* depth, const mat4f& cameraToWorld = mat4f::identity(), UINT64 timeStampColor = 0, UINT64 timeStampDepth = 0)

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

		// printf("(%lf, %lf, %lf, %lf)\n", tx, ty, tz, tp.a);
		CloudPoint px = CloudPoint(tx, ty, tz, tp.a);
		projectedPoints.push_back(px);
	}

	// nearest neighbor // unsigned short 0~65535
	unsigned short *depthMap = new unsigned short [width*height];
	ml::vec3uc *colorMap = new ml::vec3uc [width*height];


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
	for (int iw=0; iw<width; iw++){ // w=450
		for (int ih=0; ih<height; ih++){ // h=350
			// printf("[%d][%d]\n", iw, ih);
			CloudPoint nearestPoint = CloudPoint();
			double maxSqrDist = gr*gr*2 + 1; // out of a grid

			vector<int> candiPointIds = neighborPointIds[ih*width + iw];

			// neighor points of this pixel
			for (auto& pointId : candiPointIds){
				CloudPoint p = projectedPoints[pointId];
				// whether the point in 2x2 grid
				if (p.x > iw - gr && p.x < iw + gr &&
				    p.y > ih - gr && p.y < ih + gr){
					// printf("\t(%.3lf, %.3lf)\n", p.x, p.y);
					double sqrDistToCenter =
						(p.x-iw)*(p.x-iw) + (p.y-ih)*(p.y-ih) ;
					if (sqrDistToCenter < maxSqrDist){
						maxSqrDist = sqrDistToCenter;
						nearestPoint = p;
					}
				}
			}
					
			if(maxSqrDist == gr*gr*2 + 1){
				// POINT NOT FOUND
				depthMap[ih*width + iw] = 65535;
				unsigned char zeroColor[3] = {0, 0, 0};
				ml::vec3uc *pc = (ml::vec3uc*)std::malloc(sizeof(ml::vec3uc));
				memcpy(pc, &zeroColor, sizeof(ml::vec3uc));
				colorMap[ih*width + iw] = *pc;
			} else {
				depthMap[ih*width + iw] = (unsigned short)(nearestPoint.z * 1000);
				double a = nearestPoint.a;
				int i_a = (int)a;
				i_a = (i_a > 255) ? 225 : i_a;
                i_a = (i_a < 0) ? 0 : i_a;
				unsigned char ass = (unsigned char)(i_a);
				unsigned char assColor[3] = {ass, ass, ass};
				ml::vec3uc pc;
				memcpy(&pc, &assColor, sizeof(ml::vec3uc));
				colorMap[ih*width + iw] = pc;
			}
		}
	}

	histogramEq(colorMap);

	sd.addFrame(colorMap, depthMap);

	delete [] colorMap, depthMap;
}

void convertPlyToSens(vector<string>& inFiles, string outFile, ml::SensorData& sd){
	unsigned int colorWidth = width;
	unsigned int colorHeight = height;
	unsigned int depthWidth = width;
	unsigned int depthHeight = height;
	const _MSC_ calibrationColor;
	const _MSC_ calibrationDepth;
	sd.initDefault(
		colorWidth, colorHeight, depthWidth, depthHeight,
		calibrationColor, calibrationDepth
	);

	for(int i=0; i<inFiles.size(); i++){
		string file = inFiles[i];
		printf("\rConverting [%s] ... [%d/%d]", file.c_str(), i, (int)(inFiles.size())-1);
		fflush(stdout);
		vector<CloudPoint> points;
		readPly(file, points);
		convertToRGBDFrame(sd, points);
	}
	printf("\n");
	sd.saveToFile(outFile);
}

