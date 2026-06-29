import Foundation
import OSLog

enum AppLog {
    enum Category: String {
        case workerClient = "WorkerClient"
        case mockWorkerClient = "MockWorkerClient"
    }

    private static let subsystem = Bundle.main.bundleIdentifier ?? "com.flhcc.Stocket"

    static func logger(category: Category) -> Logger {
        Logger(subsystem: subsystem, category: category.rawValue)
    }
}
