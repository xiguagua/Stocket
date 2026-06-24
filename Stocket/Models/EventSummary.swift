import Foundation
import SwiftData

@Model
final class EventSummary {
    @Attribute(.unique) var accession: String
    var ticker: String
    var cik: String
    var filingType: String
    var filingDate: Date
    var importance: Int
    var itemsRaw: [String]
    var oneLineSummary: String
    var createdAt: Date
    var orphanedAt: Date?

    init(
        accession: String,
        ticker: String,
        cik: String,
        filingType: String,
        filingDate: Date,
        importance: Int,
        itemsRaw: [String],
        oneLineSummary: String,
        createdAt: Date = Date(),
        orphanedAt: Date? = nil
    ) {
        self.accession = accession
        self.ticker = ticker
        self.cik = cik
        self.filingType = filingType
        self.filingDate = filingDate
        self.importance = importance
        self.itemsRaw = itemsRaw
        self.oneLineSummary = oneLineSummary
        self.createdAt = createdAt
        self.orphanedAt = orphanedAt
    }
}
