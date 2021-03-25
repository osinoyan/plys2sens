CXX = g++
#CXX = clang++
FLAGS=-std=c++11 -g -fopenmp

main:
	# $(CXX) $(FLAGS) -o reader src/main_origin.cpp
	# $(CXX) $(FLAGS) -o sens src/main.cpp
	$(CXX) $(FLAGS) -o sens_mp src/main_MP.cpp

mp:
	$(CXX) $(FLAGS) -o mptest src/openmp_test.cpp

clean:
	rm -fr sens