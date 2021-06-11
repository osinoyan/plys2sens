CXX = g++
#CXX = clang++
FLAGS=-std=c++11 -g -fopenmp

main:
	# $(CXX) $(FLAGS) -o reader src/main_origin.cpp
	# $(CXX) $(FLAGS) -o sens src/main.cpp
	# $(CXX) $(FLAGS) -o sens_mp src/sens_MP.cpp
	# $(CXX) $(FLAGS) -o conver2dmp src/conver2dmp.cpp
	# $(CXX) $(FLAGS) -o binply2dmp src/binply2dmp.cpp
	# $(CXX) $(FLAGS) -o out_sens src/out_sens.cpp
mp:
	$(CXX) $(FLAGS) -o mptest src/openmp_test.cpp

clean:
	rm -fr sens