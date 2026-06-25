import SwiftUI
import SwiftData

struct ContentView: View {
    var body: some View {
        TabView {
            Tab("Today", systemImage: "newspaper") {
                TodayView()
            }

            Tab("Portfolio", systemImage: "list.bullet") {
                PortfolioView()
            }
        }
    }
}

#Preview {
    ContentView()
        .modelContainer(for: UserTicker.self, inMemory: true)
}
