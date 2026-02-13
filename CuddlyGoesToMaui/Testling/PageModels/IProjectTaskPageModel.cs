using CommunityToolkit.Mvvm.Input;
using Testling.Models;

namespace Testling.PageModels
{
    public interface IProjectTaskPageModel
    {
        IAsyncRelayCommand<ProjectTask> NavigateToTaskCommand { get; }
        bool IsBusy { get; }
    }
}