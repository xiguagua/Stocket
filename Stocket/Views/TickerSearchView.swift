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
                        Text(verbatim: entry.ticker)
                            .font(.headline)
                        Text(verbatim: entry.companyName)
                            .font(.caption)
                            .foregroundStyle(.secondary)
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
