import SwiftUI
import SwiftData

// MARK: - App

@main
struct StocketApp: App {
  let appContainer: ModelContainer

  init() {
    let userSchema = Schema([UserTicker.self])
    let refSchema = Schema([EventSummary.self])
    let storeDirectory = URL.applicationSupportDirectory
    let userConfig = ModelConfiguration(
      "UserPrivate",
      schema: userSchema,
      url: storeDirectory.appending(path: "UserPrivate.store")
    )
    let refConfig = ModelConfiguration(
      "Reference",
      schema: refSchema,
      url: storeDirectory.appending(path: "Reference.store")
    )

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
