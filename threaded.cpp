#include <bits/stdc++.h>
using namespace std;

#define walk_ub 1000000
mutex m1;
long double ans = 0;

void random_walk(double price, int num_days) {
    thread_local mt19937 gen(random_device{}());
    uniform_real_distribution<> dist(0, 1);

    for (int i = 0; i < num_days; ++i) {
        if (dist(gen) >= 0.5) price *= 1.01;
        else price *= 0.99;
    }

    lock_guard<mutex> lg(m1);
    ans += price;
}

void helper(int t) {
    for (int i = 0; i < t; ++i) {
        random_walk(100, 100);
    }
}

int main() {
    auto start = chrono::high_resolution_clock::now();
    int nT = thread::hardware_concurrency();
    int iter = walk_ub / nT;

    vector<thread> threads;
    threads.reserve(nT);

    for (int i = 0; i < nT; ++i) {
        threads.emplace_back(helper, iter);
    }

    for (auto &t : threads) {
        t.join();
    }

    // THis isnt dynamic schedulign though

    cout << ans / walk_ub << "\n";
    auto end = chrono::high_resolution_clock::now();
    
}
