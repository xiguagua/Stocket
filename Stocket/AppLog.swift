import Foundation
import OSLog

enum AppLog {
    private static let subsystem = Bundle.main.bundleIdentifier ?? "com.flhcc.Stocket"

    static func logger(category: String) -> Logger {
        Logger(subsystem: subsystem, category: category)
    }
}
