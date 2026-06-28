import SwiftUI

struct TickerSearchView: View {
    @State private var query = ""
    @State private var allEntries: [TickerEntry] = []
    @State private var results: [TickerEntry] = []
    let onSelect: (TickerEntry) -> Void

    private let popularTickers = ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "META"]

    var body: some View {
        NavigationStack {
            Group {
                if query.isEmpty {
                    VStack(spacing: Theme.Spacing.pt20.rawValue) {
                        Spacer()

                        Image(systemName: "magnifyingglass")
                            .font(.system(size: 48))
                            .foregroundStyle(.secondary)
                            .symbolEffect(.bounce, value: query.isEmpty)

                        VStack(spacing: Theme.Spacing.pt8.rawValue) {
                            Text("ticker.search.guidance.title")
                                .font(.headline)
                            Text("ticker.search.guidance.description")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal, Theme.Spacing.pt32.rawValue)
                        }

                        VStack(alignment: .leading, spacing: Theme.Spacing.pt12.rawValue) {
                            Text("ticker.search.popular.title")
                                .font(.caption)
                                .fontWeight(.bold)
                                .foregroundStyle(.secondary)
                                .padding(.horizontal, Theme.Spacing.pt16.rawValue)

                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: Theme.Spacing.pt8.rawValue) {
                                    ForEach(popularTickers, id: \.self) { ticker in
                                        Button {
                                            query = ticker
                                        } label: {
                                            Text(verbatim: ticker)
                                                .font(.subheadline)
                                                .fontWeight(.medium)
                                                .padding(.horizontal, Theme.Spacing.pt16.rawValue)
                                                .padding(.vertical, Theme.Spacing.pt8.rawValue)
                                                .background(Color.blue.opacity(0.15), in: Capsule())
                                        }
                                    }
                                }
                                .padding(.horizontal, Theme.Spacing.pt16.rawValue)
                            }
                        }
                        .padding(.top, Theme.Spacing.pt20.rawValue)

                        Spacer()
                    }
                } else {
                    List(results) { entry in
                        Button { onSelect(entry) } label: {
                            VStack(alignment: .leading) {
                                Text(verbatim: entry.ticker)
                                    .font(.headline)
                                Text(verbatim: entry.companyName)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
            .searchable(text: $query, prompt: Text("ticker.search.prompt"))
            .onChange(of: query) { _, newValue in
                results = TickerLookup.search(newValue, in: allEntries)
            }
            .navigationTitle("ticker.search.title")
            .navigationBarTitleDisplayMode(.inline)
        }
        .onAppear {
            allEntries = TickerLookup.loadAll()
        }
    }
}

#Preview {
    TickerSearchView { _ in }
}
