#include <bits/stdc++.h>
using namespace std;

#define walk_ub 1000000

int random_walk(double price, int num_days) {
    random_device rd;           
    mt19937 gen(rd());          
    uniform_real_distribution<> dist(0, 1);

    for (int i = 0; i < num_days; ++i) {
        if (dist(gen) >= 0.5) price *= 1.01;
        else price *= 0.99;
    }

    return price;
}   

int main() {
    auto start = chrono::high_resolution_clock::now();
    long double pred = 0;;

    // Normal - 15.47 secs

    // for (int i = 0; i < walk_ub; ++i) {
    //     pred += random_walk(100, 100);
    // }

    // OpenMP - 1.85 secs
    // and using reduction is same as using a temp var and then a critical section

    // #pragma omp parallel for schedule(dynamic) reduction(+:pred)
    // for (int i = 0; i < walk_ub; ++i) {
    //     pred += random_walk(100, 100);
    // }
    
    cout << pred / walk_ub << '\n';
    auto end = chrono::high_resolution_clock::now();
    chrono::duration<double> duration = end - start;
    cout << duration.count();
}
