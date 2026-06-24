import Foundation
import SwiftData

enum EventSyncer {
    static func sync(tickers: [UserTicker], referenceContext: ModelContext) async {
        for userTicker in tickers {
            await syncTicker(userTicker, referenceContext: referenceContext)
        }
    }

    static func syncTicker(_ userTicker: UserTicker, referenceContext: ModelContext) async {
        let latestDate = fetchLatestEventDate(for: userTicker.ticker, in: referenceContext)

        do {
            let dtos = try await WorkerClient.shared.fetchEvents(
                ticker: userTicker.ticker,
                since: latestDate
            )
            upsertEvents(dtos, ticker: userTicker.ticker, cik: userTicker.cik, in: referenceContext)
        } catch {
            // Silent fail — local data still renders
        }
    }

    private static func fetchLatestEventDate(for ticker: String, in context: ModelContext) -> Date? {
        let descriptor = FetchDescriptor<EventSummary>(
            predicate: #Predicate { $0.ticker == ticker },
            sortBy: [SortDescriptor(\.filingDate, order: .reverse)]
        )
        let events = (try? context.fetch(descriptor)) ?? []
        return events.first?.filingDate
    }

    private static func upsertEvents(
        _ dtos: [WorkerClient.EventDTO],
        ticker: String,
        cik: String,
        in context: ModelContext
    ) {
        let dateFormatter = ISO8601DateFormatter()

        for dto in dtos {
            let accession = dto.accession
            let descriptor = FetchDescriptor<EventSummary>(
                predicate: #Predicate { $0.accession == accession }
            )
            let existing = (try? context.fetch(descriptor))?.first

            let filingDate = dateFormatter.date(from: dto.filingDate) ?? Date()
            let createdAt = dateFormatter.date(from: dto.createdAt) ?? Date()

            if let existing {
                existing.filingDate = filingDate
                existing.importance = dto.importance
                existing.itemsRaw = dto.items
                existing.oneLineSummary = dto.oneLineSummary
                existing.createdAt = createdAt
            } else {
                let event = EventSummary(
                    accession: accession,
                    ticker: dto.ticker,
                    cik: dto.cik,
                    filingType: dto.filingType,
                    filingDate: filingDate,
                    importance: dto.importance,
                    itemsRaw: dto.items,
                    oneLineSummary: dto.oneLineSummary,
                    createdAt: createdAt
                )
                context.insert(event)
            }
        }

        try? context.save()
    }
}
