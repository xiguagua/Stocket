import SwiftUI
import SwiftData

struct TodayView: View {
    @Environment(\.modelContext) private var userContext
    @Environment(\.referenceModelContext) private var referenceContext

    @Query(sort: \UserTicker.ticker) private var tickers: [UserTicker]

    @State private var events: [EventSummary] = []
    @State private var lastSynced: Date?
    @State private var isSyncing = false

    private var syncKey: String {
        tickers.map(\.ticker).sorted().joined(separator: ",")
    }

    private let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateStyle = .medium
        f.timeStyle = .short
        return f
    }()

    var body: some View {
        NavigationStack {
            Group {
                if events.isEmpty {
                    ContentUnavailableView(
                        "No new events today",
                        systemImage: "newspaper",
                        description: Text(lastSynced.map { "Last updated \(dateFormatter.string(from: $0))" } ?? "Events for your watchlist will appear here")
                    )
                } else {
                    List(events) { event in
                        EventRow(event: event)
                    }
                }
            }
            .navigationTitle("Today")
            .task(id: syncKey) { await loadAndSync() }
        }
    }

    private func loadAndSync() async {
        // Render local first
        loadLocalEvents()

        // Background sync
        guard let refContext = referenceContext, !tickers.isEmpty, !isSyncing else { return }
        isSyncing = true
        await EventSyncer.sync(tickers: tickers, referenceContext: refContext)
        loadLocalEvents()
        lastSynced = Date()
        isSyncing = false
    }

    private func loadLocalEvents() {
        guard let refContext = referenceContext else { return }
        let tickerNames = Set(tickers.map(\.ticker))
        let descriptor = FetchDescriptor<EventSummary>(
            sortBy: [SortDescriptor(\.filingDate, order: .reverse)]
        )
        let all = (try? refContext.fetch(descriptor)) ?? []
        events = all.filter { tickerNames.contains($0.ticker) }
    }
}

private struct EventRow: View {
    let event: EventSummary

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(event.ticker)
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundStyle(.secondary)
                Spacer()
                Text(event.filingType)
                    .font(.caption2)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.blue.opacity(0.15), in: Capsule())
            }
            Text(event.oneLineSummary)
                .font(.body)
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    TodayView()
        .modelContainer(for: UserTicker.self, inMemory: true)
}
