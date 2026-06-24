import SwiftUI

struct TickerSearchView: View {
    @State private var query = ""
    @State private var allEntries: [TickerEntry] = []
    @State private var results: [TickerEntry] = []
    let onSelect: (TickerEntry) -> Void

    var body: some View {
        NavigationStack {
            List(results) { entry in
                Button { onSelect(entry) } label: {
                    VStack(alignment: .leading) {
                        Text(entry.ticker)
                            .font(.headline)
                        Text(entry.companyName)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .searchable(text: $query, prompt: "Search ticker or company name")
            .onChange(of: query) { _, newValue in
                results = TickerLookup.search(newValue, in: allEntries)
            }
            .navigationTitle("Add Ticker")
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
