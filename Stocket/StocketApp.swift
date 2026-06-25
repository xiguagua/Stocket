import SwiftUI
import SwiftData

// MARK: - App

@main
struct StocketApp: App {
  let appContainer: ModelContainer

  init() {
    let userSchema = Schema([UserTicker.self])
    let userConfig = ModelConfiguration(schema: userSchema, isStoredInMemoryOnly: false)
    let refSchema = Schema([EventSummary.self])
    let refConfig = ModelConfiguration(schema: refSchema, isStoredInMemoryOnly: false)

    let appSchema = Schema([UserTicker.self, EventSummary.self])
    do {
      appContainer = try ModelContainer(for: appSchema, configurations: [userConfig, refConfig])
    } catch {
      fatalError("Could not create ModelContainer: \(error)")
    }
  }

  var body: some Scene {
    WindowGroup {
      ContentView()
    }
    .modelContainer(appContainer)
  }
}
