#include <iostream>
#include <thread>
#include <chrono>
using namespace std;

#define lim 10000000
int coun = 0;

mutex m1, m2;

void foo1() {

    for (int i = 0; i < lim; ++i) {
        while (true) {
            if (m1.try_lock()) {
                if (m2.try_lock()) {
                    ++coun;
                    m1.unlock();
                    m2.unlock();
                    break;
                }
                else {
                    m1.unlock();
                }
            }
        }
    }
}

void foo2() {


    for (int i = 0; i < lim; ++i) {
        while (true) {
            if (m2.try_lock()) {
                if (m1.try_lock()) {
                    ++coun;
                    m2.unlock();
                    m1.unlock();
                    break;
                }
                else {
                    m2.unlock();
                }
            }
        }
    }
}


int main() {
    auto start = chrono::high_resolution_clock::now();
    thread t1(foo1);
    thread t2(foo2);

    t1.join();
    t2.join();
    
    auto end = chrono::high_resolution_clock::now();
    chrono::duration<double> duration = end - start;
    cout << duration.count() << '\n';
    cout << coun;
}

// thread - join, detach, else termiante()
// jthread + stop_request, stop_token (cpp 20)
// mutex - lock, unlock, lock_guard 

// no atomicity or locks gives random answers
// atomicity seems much slower on shared var (upto 10 times for large lim)
    // caching (?) - yep, cache line blocking - MESI protocol

// deadlock 
    // two jthreads stopped forever even for lim = 10000000 for 1,2 and 2,1 locking
    
    // lock ordering works 3.5 sec
    // atomic with 2 threads gives 36 seconds?

    // if-then (breaking hold and await) works 6.6 seconds and gives correct ans only upon using while
    // if while isn't used, some iterations are skipped and we dont get 2e7 I think
