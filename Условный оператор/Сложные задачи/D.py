"""
    #include <iostream>

using namespace std;

int main() {
    // Оптимизация ввода/вывода
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    
    long long n, m;
    if (cin >> n >> m) {
        // Базовое количество отрезков (каждый должен быть пройден хотя бы раз)
        long long edges = 2LL * n * m + n + m;
        
        // Добавочные отрезки для корректировки нечетных вершин (паросочетание)
        long long added = 0;
        
        if ((n % 2 != 0 && m % 2 != 0) || n == 1 || m == 1) {
            added = n + m - 2;
        } else {
            added = n + m;
        }
        
        // Время равно общему количеству пройденных участков (по 1 мин на каждый)
        cout << edges + added << "\n";
    }
    
    return 0;
}
"""