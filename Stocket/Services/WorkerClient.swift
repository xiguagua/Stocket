import Foundation

actor WorkerClient {
    static let shared = WorkerClient()

    private let baseURL: URL
    private let session: URLSession

    init() {
        let host = ProcessInfo.processInfo.environment["WORKER_HOST"] ?? "localhost"
        let port = ProcessInfo.processInfo.environment["WORKER_PORT"] ?? "8787"
        self.baseURL = URL(string: "http://\(host):\(port)")!
        self.session = URLSession(configuration: .ephemeral)
    }

    struct WatchlistPayload: Encodable {
        let userId: String
        let ticker: String
        let cik: String
        let relation: String
    }

    struct EventDTO: Decodable {
        let accession: String
        let ticker: String
        let cik: String
        let filingType: String
        let filingDate: String
        let importance: Int
        let items: [String]
        let oneLineSummary: String
        let createdAt: String
    }

    func postWatchlist(userId: String, ticker: String, cik: String, relation: String) async throws {
        let payload = WatchlistPayload(userId: userId, ticker: ticker, cik: cik, relation: relation)
        var request = URLRequest(url: baseURL.appending(path: "watchlist"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(payload)
        _ = try await session.data(for: request)
    }

    func fetchEvents(ticker: String, since: Date?) async throws -> [EventDTO] {
        var url = baseURL.appending(path: "tickers").appending(path: ticker.uppercased()).appending(path: "events")
        if let since {
            let iso = ISO8601DateFormatter().string(from: since)
            url = url.appending(queryItems: [URLQueryItem(name: "since", value: iso)])
        }
        let (data, _) = try await session.data(from: url)
        return try JSONDecoder().decode([EventDTO].self, from: data)
    }
}
