import Foundation
import SwiftData

enum Relation: String, Codable, CaseIterable {
    case position
    case watching
}

@Model
final class UserTicker {
    var ticker: String
    var cik: String
    var companyName: String
    var relation: Relation
    var addedAt: Date

    init(ticker: String, cik: String, companyName: String, relation: Relation = .watching, addedAt: Date = Date()) {
        self.ticker = ticker
        self.cik = cik
        self.companyName = companyName
        self.relation = relation
        self.addedAt = addedAt
    }
}
