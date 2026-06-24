import Foundation

struct TickerEntry: Identifiable, Hashable {
    let id: String
    let ticker: String
    let cik: String
    let companyName: String
}

enum TickerLookup {
    static func loadAll() -> [TickerEntry] {
        guard let url = Bundle.main.url(forResource: "company_tickers", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: [String: Any]]
        else {
            return []
        }

        return json.compactMap { _, value in
            guard let ticker = value["ticker"] as? String,
                  let cik = value["cik_str"] as? Int,
                  let title = value["title"] as? String
            else { return nil }
            return TickerEntry(id: ticker, ticker: ticker, cik: String(cik), companyName: title)
        }
    }

    static func search(_ query: String, in entries: [TickerEntry]) -> [TickerEntry] {
        let q = query.uppercased().trimmingCharacters(in: .whitespaces)
        guard !q.isEmpty else { return [] }

        let prefixMatches = entries.filter { $0.ticker.hasPrefix(q) }
        let nameMatches = entries.filter {
            !$0.ticker.hasPrefix(q) && $0.companyName.uppercased().contains(q)
        }

        let combined = prefixMatches + nameMatches
        return Array(combined.prefix(30))
    }
}
