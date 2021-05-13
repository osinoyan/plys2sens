// ------------ CREATED AT 2021/05/05 BY LYWANG ---------------------
// ---------- FOR CONVERTING [SHARP-NET OUTPUT PRE_DEPTH] TO [.SENS] FILE ------------------
// ---------- OPENMP VERSION ------------------

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
void histogramEq(ml::vec3uc *colorMap);
void readPreDepth(string d_file, string r_file, ml::SensorData& sd);
void convertPlyToSens(vector<string>& d_files, vector<string>& r_files, string outFile, ml::SensorData& sd);

// MAIN ----------------------------------------------------
int main(int argc, char* argv[])
{
	try {
		//non-cached read
		std::string inPath = ".";
		std::string outFile = "scene_00.sens";

		if (argc == 3) {
			inPath = std::string(argv[1]);
			outFile = std::string(argv[2]);
		} else {
			std::cout << "run ./out_sens <path/to/output> out_lab05.sens";
			exit(0);
		}

		if (inPath[inPath.size()-1] != '/') inPath += '/';
		std::string depthPath = inPath + "pre_depth/";
		std::string rgbPath = inPath + "rgb_input/";
		std::cout << "inPath =\t" << inPath << std::endl;
		std::cout << "depthPath =\t" << depthPath << std::endl;
		std::cout << "rgbPath =\t" << rgbPath << std::endl;
		std::cout << "outFile =\t" << outFile << std::endl;

		PAUSE


		/////////////////////////////////////////////////////////////////////////
		// Get all files
		
		DIR *dir;
		struct dirent *ent;
		vector<string> d_files;
		if ((dir = opendir (depthPath.c_str())) != NULL) {
			/* print all the files and directories within directory */
			while ((ent = readdir (dir)) != NULL) {
				if(ent->d_name[0] != '.'){
					string file_path = depthPath + ent->d_name;
					d_files.push_back(file_path);
				}
			}
			closedir (dir);
		} else {
			/* could not open directory */
			perror ("");
			return EXIT_FAILURE;
		}

		vector<string> r_files;
		if ((dir = opendir (rgbPath.c_str())) != NULL) {
			/* print all the files and directories within directory */
			while ((ent = readdir (dir)) != NULL) {
				if(ent->d_name[0] != '.'){
					string file_path = rgbPath + ent->d_name;
					r_files.push_back(file_path);
				}
			}
			closedir (dir);
		} else {
			/* could not open directory */
			perror ("");
			return EXIT_FAILURE;
		}

		/////////////////////////////////////////////////////////////////////////
		sort(d_files.begin(), d_files.end());
		sort(r_files.begin(), r_files.end());
		std::cout << "loading from pre_depth files... \n";
		ml::SensorData sd = ml::SensorData();
		convertPlyToSens(d_files, r_files, outFile, sd);

		//////////////////////////////////////////////////////////////////////


		std::cout << "done!" << std::endl;

		std::cout << sd << std::endl;

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

// FUNCTIONS -----------------------------------------------
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

void readPreDepth(string d_file, string r_file, ml::SensorData& sd){
	unsigned short *depthMap = new unsigned short [width*height]; // 350x450
	ml::vec3uc *colorMap = new ml::vec3uc [width*height];

	//////////////////////////////////////////////////////////////////
	// get rgb map
	ifstream r_ifs(r_file, ios::in | ios::binary);

	float rmap[384][512] = {0.0f};
	r_ifs.read((char *) &rmap, sizeof(rmap));
	// cout << r_ifs.gcount() << " bytes read\n";

	for (int ih=0; ih<384; ih++){
		for (int iw=0; iw<512; iw++){
			int oh = ih - 17;
			int ow = iw - 31;
			bool isPadding = (oh < 0) || (oh >= 350) || (ow < 0) || (ow >= 450);
			if (isPadding) continue;

			double a = rmap[ih][iw] * 255.0;
			int i_a = (int)a;
			i_a = (i_a > 255) ? 225 : i_a;
			i_a = (i_a < 0) ? 0 : i_a;
			unsigned char rgb = (unsigned char)(i_a);
			unsigned char rgbColor[3] = {rgb, rgb, rgb};
			ml::vec3uc pc;
			memcpy(&pc, &rgbColor, sizeof(ml::vec3uc));
			colorMap[oh*width + ow] = pc;
		}
	}
	r_ifs.close();

	//////////////////////////////////////////////////////////////////
	// get depth map
	ifstream ifs(d_file, ios::in | ios::binary);

	float dmap[384][512] = {0.0f};
	ifs.read((char *) &dmap, sizeof(dmap));
	// cout << ifs.gcount() << " bytes read\n";

	for (int ih=0; ih<384; ih++){
		for (int iw=0; iw<512; iw++){
			int oh = ih - 17;
			int ow = iw - 31;
			bool isPadding = (oh < 0) || (oh >= 350) || (ow < 0) || (ow >= 450);
			if (isPadding) continue;
			depthMap[oh*width + ow] = (unsigned short)(dmap[ih][iw] * 1000);
		}
	}
	ifs.close();
	
	histogramEq(colorMap);
	sd.addFrame(colorMap, depthMap);
	delete [] colorMap, depthMap;
}

void convertPlyToSens(vector<string>& d_files, vector<string>& r_files, string outFile, ml::SensorData& sd){
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

	for(int i=0; i<d_files.size(); i++){
		string d_file = d_files[i];
		string r_file = r_files[i];
		printf("Converting [%s] ... [%d/%d]\n", d_file.c_str(), i, (int)(d_files.size())-1);
		readPreDepth(d_file, r_file, sd);
	}
	sd.saveToFile(outFile);
}

