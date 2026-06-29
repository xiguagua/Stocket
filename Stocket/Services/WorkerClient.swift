import Foundation
import OSLog

// MARK: - Protocol

protocol WorkerClientProtocol: Sendable {
    func postWatchlist(userId: String, ticker: String, cik: String, relation: String) async throws
    func fetchEvents(ticker: String, since: Date?) async throws -> [WorkerClient.EventDTO]
}

// MARK: - Namespace & Dispatcher

enum WorkerClient {
    private static let logger = AppLog.logger(category: .workerClient)

    static let shared: any WorkerClientProtocol = {
        #if DEBUG
        if ProcessInfo.processInfo.environment["USE_MOCK"] == "true" {
            logger.debug("Initializing MockWorkerClient")
            return MockWorkerClient()
        }
        #endif
        logger.debug("Initializing RealWorkerClient")
        return RealWorkerClient()
    }()

    struct EventDTO: Codable {
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
}

// MARK: - Real Implementation

struct RealWorkerClient: WorkerClientProtocol {
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

    func postWatchlist(userId: String, ticker: String, cik: String, relation: String) async throws {
        let payload = WatchlistPayload(userId: userId, ticker: ticker, cik: cik, relation: relation)
        var request = URLRequest(url: baseURL.appending(path: "watchlist"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(payload)
        _ = try await session.data(for: request)
    }

    func fetchEvents(ticker: String, since: Date?) async throws -> [WorkerClient.EventDTO] {
        var url = baseURL.appending(path: "tickers").appending(path: ticker.uppercased()).appending(path: "events")
        if let since {
            let iso = ISO8601DateFormatter().string(from: since)
            url = url.appending(queryItems: [URLQueryItem(name: "since", value: iso)])
        }
        let (data, _) = try await session.data(from: url)
        return try JSONDecoder().decode([WorkerClient.EventDTO].self, from: data)
    }
}

// MARK: - Mock Implementation

struct MockWorkerClient: WorkerClientProtocol {
    private static let logger = AppLog.logger(category: .mockWorkerClient)

    func postWatchlist(userId: String, ticker: String, cik: String, relation: String) async throws {
        Self.logger.debug("postWatchlist ticker: \(ticker, privacy: .public), cik: \(cik, privacy: .private), user: \(userId, privacy: .private), relation: \(relation, privacy: .public)")
        try await Task.sleep(for: .milliseconds(150)) // simulate network delay
    }

    func fetchEvents(ticker: String, since: Date?) async throws -> [WorkerClient.EventDTO] {
        Self.logger.debug("fetchEvents ticker: \(ticker, privacy: .public), since: \(String(describing: since), privacy: .public)")
        try await Task.sleep(for: .milliseconds(200)) // simulate network delay

        let formatter = ISO8601DateFormatter()
        let now = Date()
        let yesterday = Calendar.current.date(byAdding: .day, value: -1, to: now) ?? now

        let event1 = WorkerClient.EventDTO(
            accession: "mock-\(ticker)-8k-\(Int(now.timeIntervalSince1970))",
            ticker: ticker.uppercased(),
            cik: "0000000000",
            filingType: "8-K",
            filingDate: formatter.string(from: now),
            importance: 5,
            items: ["1.01"],
            oneLineSummary: "Company announced a material merger or acquisition transaction.",
            createdAt: formatter.string(from: now)
        )

        let event2 = WorkerClient.EventDTO(
            accession: "mock-\(ticker)-8k-\(Int(yesterday.timeIntervalSince1970))",
            ticker: ticker.uppercased(),
            cik: "0000000000",
            filingType: "8-K",
            filingDate: formatter.string(from: yesterday),
            importance: 3,
            items: ["2.02"],
            oneLineSummary: "Company reported quarterly financial results.",
            createdAt: formatter.string(from: yesterday)
        )

        var result = [event1, event2]
        if let since {
            result = result.filter { dto in
                guard let date = formatter.date(from: dto.filingDate) else { return false }
                return date > since
            }
        }
        return result
    }
}
