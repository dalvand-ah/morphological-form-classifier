import ComparePages from './components/ComparePages'

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Profile Lab</h1>
        <p>
          A small demo of the classifier in this project: scanned form pages are matched by comparing a
          1D "line profile" extracted with dilation/erosion, not by a trained neural network.
        </p>
      </header>

      <ComparePages />
    </div>
  )
}
