CXX = g++
#CXX = clang++
FLAGS=-std=c++11 -g

main:
	# $(CXX) $(FLAGS) -o reader src/main_origin.cpp
	$(CXX) $(FLAGS) -o sens src/main.cpp

clean:
	rm -fr sens