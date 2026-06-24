import SwiftUI
import SwiftData

// MARK: - Reference ModelContext Environment

private struct ReferenceModelContextKey: EnvironmentKey {
    static let defaultValue: ModelContext? = nil
}

extension EnvironmentValues {
    var referenceModelContext: ModelContext? {
        get { self[ReferenceModelContextKey.self] }
        set { self[ReferenceModelContextKey.self] = newValue }
    }
}

// MARK: - App

@main
struct StocketApp: App {
    let userContainer: ModelContainer
    let referenceContainer: ModelContainer

    init() {
        let userSchema = Schema([UserTicker.self])
        let userConfig = ModelConfiguration(schema: userSchema, isStoredInMemoryOnly: false)
        do {
            userContainer = try ModelContainer(for: userSchema, configurations: [userConfig])
        } catch {
            fatalError("Could not create UserContainer: \(error)")
        }

        let refSchema = Schema([EventSummary.self])
        let refConfig = ModelConfiguration(schema: refSchema, isStoredInMemoryOnly: false)
        do {
            referenceContainer = try ModelContainer(for: refSchema, configurations: [refConfig])
        } catch {
            fatalError("Could not create ReferenceContainer: \(error)")
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(\.referenceModelContext, referenceContainer.mainContext)
        }
        .modelContainer(userContainer)
    }
}
