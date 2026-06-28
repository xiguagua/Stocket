import SwiftUI
import SwiftData

struct PortfolioView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \UserTicker.ticker) private var tickers: [UserTicker]

    @State private var showingSearch = false
    @State private var postingError: String?

    var body: some View {
        NavigationStack {
            Group {
                if tickers.isEmpty {
                    ContentUnavailableView(
                        "portfolio.empty.title",
                        systemImage: "chart.line.uptrend.xyaxis",
                        description: Text("portfolio.empty.description")
                    )
                } else {
                    List {
                        Section("portfolio.positions.section") {
                            ForEach(tickers.filter { $0.relation == .position }) { ticker in
                                tickerRow(ticker)
                            }
                        }
                        Section("portfolio.watching.section") {
                            ForEach(tickers.filter { $0.relation == .watching }) { ticker in
                                tickerRow(ticker)
                            }
                        }
                    }
                }
            }
            .navigationTitle("portfolio.title")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button { showingSearch = true } label: {
                        Image(systemName: "plus")
                    }
                    .accessibilityIdentifier("portfolio.addTicker")
                }
            }
            .sheet(isPresented: $showingSearch) {
                TickerSearchView { entry in
                    addTicker(entry)
                    showingSearch = false
                }
            }
        }
    }

    @ViewBuilder
    private func tickerRow(_ ticker: UserTicker) -> some View {
        HStack {
            VStack(alignment: .leading) {
                Text(verbatim: ticker.ticker).font(.headline)
                Text(verbatim: ticker.companyName).font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            if ticker.relation == .position {
                Text("portfolio.position.badge").font(.caption2)
                    .padding(.horizontal, pt8)
                    .padding(.vertical, pt2)
                    .background(Color.green.opacity(0.2), in: Capsule())
            }
        }
    }

    private func addTicker(_ entry: TickerEntry) {
        guard !tickers.contains(where: { $0.ticker == entry.ticker }) else { return }
        let userTicker = UserTicker(
            ticker: entry.ticker,
            cik: entry.cik,
            companyName: entry.companyName,
            relation: .watching
        )
        modelContext.insert(userTicker)

        do {
            try modelContext.save()
        } catch {
            postingError = error.localizedDescription
            return
        }

        Task {
            do {
                try await WorkerClient.shared.postWatchlist(
                    userId: "local-user",
                    ticker: entry.ticker,
                    cik: entry.cik,
                    relation: "watching"
                )
            } catch {
                postingError = error.localizedDescription
            }
        }
    }
}

#Preview {
    PortfolioView()
        .modelContainer(for: UserTicker.self, inMemory: true)
}
